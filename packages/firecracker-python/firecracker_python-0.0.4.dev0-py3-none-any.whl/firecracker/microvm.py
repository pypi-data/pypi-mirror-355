import os
import sys
import time
import json
import psutil
import select
import termios
import tty
import requests
import paramiko.ssh_exception
from http import HTTPStatus
from paramiko import SSHClient, AutoAddPolicy
from typing import Tuple, List, Dict
from contextlib import closing
from firecracker.config import MicroVMConfig
from firecracker.api import Api
from firecracker.logger import Logger
from firecracker.network import NetworkManager
from firecracker.process import ProcessManager
from firecracker.vmm import VMMManager
from firecracker.utils import run, get_public_ip, validate_ip_address, generate_id, generate_name, generate_mac_address
from firecracker.exceptions import APIError, VMMError, ConfigurationError, ProcessError


class MicroVM:
    """A class to manage Firecracker microVMs.

    Args:
        id (str, optional): ID for the MicroVM
    """
    def __init__(self, name: str = None, kernel_file: str = None, initrd_file: str = None, init_file: str = None,
                 base_rootfs: str = None, rootfs_url: str = None, overlayfs: bool = False, overlayfs_file: str = None,
                 vcpu: int = None, memory: int = None, ip_addr: str = None, bridge: bool = None, bridge_name: str = None,
                 mmds_enabled: bool = None, mmds_ip: str = None, user_data: str = None, user_data_file: str = None,
                 labels: dict = None, expose_ports: bool = False, host_port: int = None, dest_port: int = None,
                 verbose: bool = False, level: str = "INFO") -> None:
        """Initialize a new MicroVM instance with configuration."""
        self._microvm_id = generate_id()
        self._microvm_name = generate_name() if name is None else name

        self._config = MicroVMConfig()
        self._config.verbose = verbose
        self._logger = Logger(level=level, verbose=verbose)
        self._logger.set_level(level)

        self._network = NetworkManager(verbose=verbose, level=level)
        self._process = ProcessManager(verbose=verbose, level=level)
        self._vmm = VMMManager(verbose=verbose, level=level)

        self._vcpu = vcpu or self._config.vcpu
        self._memory = int(self._convert_memory_size(memory or self._config.memory))
        self._mmds_enabled = mmds_enabled if mmds_enabled is not None else self._config.mmds_enabled
        self._mmds_ip = mmds_ip or self._config.mmds_ip

        if not isinstance(self._vcpu, (int, float)) or self._vcpu <= 0:
            raise ValueError("vcpu must be a positive number")

        if user_data_file and user_data:
            raise ValueError("Cannot specify both user_data and user_data_file. Use only one of them.")
        if user_data_file:
            if not os.path.exists(user_data_file):
                print(f"User data file not found: {user_data_file}")
            with open(user_data_file, 'r') as f:
                self._user_data = f.read()
        else:
            self._user_data = user_data

        self._labels = labels or {}

        self._iface_name = self._network.get_interface_name()
        self._host_dev_name = f"tap_{self._microvm_id}"
        self._mac_addr = generate_mac_address()
        if ip_addr:
            validate_ip_address(ip_addr)
            self._ip_addr = ip_addr
            if self._network.detect_cidr_conflict(self._ip_addr, 24):
                self._ip_addr = self._network.suggest_non_conflicting_ip(self._ip_addr, 24)
        else:
            self._ip_addr = self._config.ip_addr
        self._gateway_ip = self._network.get_gateway_ip(self._ip_addr)
        self._bridge = bridge if bridge is not None else self._config.bridge
        self._bridge_name = bridge_name or self._config.bridge_name

        self._socket_file = f"{self._config.data_path}/{self._microvm_id}/firecracker.socket"
        self._vmm_dir = f"{self._config.data_path}/{self._microvm_id}"
        self._log_dir = f"{self._vmm_dir}/logs"
        self._rootfs_dir = f"{self._vmm_dir}/rootfs"

        self._kernel_file = kernel_file or self._config.kernel_file
        if not os.path.exists(self._kernel_file):
            print(f"Kernel file not found: {self._kernel_file}")
        self._initrd_file = initrd_file or self._config.initrd_file
        if self._initrd_file:
            if not os.path.exists(self._initrd_file):
                print(f"Initrd file not found: {self._initrd_file}")
        self._init_file = init_file or self._config.init_file
        if rootfs_url:
            self._base_rootfs = self._download_rootfs(rootfs_url)
        else:
            self._base_rootfs = base_rootfs or self._config.base_rootfs
        base_rootfs_name = os.path.basename(self._base_rootfs.replace('./', ''))
        self._rootfs_file = os.path.join(self._rootfs_dir, base_rootfs_name)

        self._overlayfs = overlayfs or self._config.overlayfs
        if self._overlayfs:
            self._overlayfs_file = overlayfs_file or os.path.join(self._rootfs_dir, "overlayfs.ext4")
            self._overlayfs_name = os.path.basename(self._overlayfs_file.replace('./', ''))
            self._overlayfs_dir = os.path.join(self._rootfs_dir, self._overlayfs_name)

        self._ssh_client = SSHClient()
        self._expose_ports = expose_ports
        self._host_ip = get_public_ip()
        self._host_port = self._parse_ports(host_port)
        self._dest_port = self._parse_ports(dest_port)

        self._api = self._vmm.get_api(self._microvm_id)

    @staticmethod
    def list() -> List[Dict]:
        """List all running Firecracker VMs.

        Returns:
            List[Dict]: List of dictionaries containing VMM details
        """
        vmm_manager = VMMManager()
        return vmm_manager.list_vmm()

    def find(self, state=None, labels=None):
        """Find a VMM by ID or labels.

        Args:
            state (str, optional): State of the VMM to find.
            labels (dict, optional): Labels to filter VMMs by.
        
        Returns:
            str: ID of the found VMM or error message.
        """
        if state:
            return self._vmm.find_vmm_by_labels(state, labels)
        else:
            return "No state provided"

    def config(self, id=None):
        """Get the configuration for the current VMM or a specific VMM.

        Args:
            id (str, optional): ID of the VMM to query. If not provided,
                uses the current VMM's ID.

        Returns:
            dict: Response from the VMM configuration endpoint or error message.
        """
        id = id if id else self._microvm_id
        if not id:
            return "No VMM ID specified for checking configuration"
        return self._vmm.get_vmm_config(id)

    def inspect(self, id=None):
        """Inspect a VMM by ID.

        Args:
            id (str, optional): ID of the VMM to inspect. If not provided,
                uses the current VMM's ID.
        """
        id = id if id else self._microvm_id

        if not id:
            return f"VMM with ID {id} does not exist"

        config_file = f"{self._config.data_path}/{id}/config.json"
        if not os.path.exists(config_file):
            return "VMM ID not exist"

        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                return config
        except Exception as e:
            raise VMMError(f"Failed to inspect VMM {id}: {str(e)}")

    def status(self, id=None):
        """Get the status of the current VMM or a specific VMM.

        Args:
            id (str, optional): ID of the VMM to check. If not provided,
                uses the current VMM's ID.
        """
        id = id if id else self._microvm_id
        if not id:
            return "No VMM ID specified for checking status"
        
        try:
            with open(f"{self._config.data_path}/{id}/config.json", "r") as f:
                config = json.load(f)
                if config['State']['Running']:
                    return f"VMM {id} is running"
                elif config['State']['Paused']:
                    return f"VMM {id} is paused"

        except Exception as e:
            raise VMMError(f"Failed to get status for VMM {id}: {str(e)}")

    def create(self) -> dict:
        vmm_dir = f"{self._config.data_path}/{self._microvm_id}"
        if os.path.exists(vmm_dir):
            return f"VMM with ID {self._microvm_id} already exists"

        try:
            if self._vmm.check_network_overlap(self._ip_addr):
                return f"IP address {self._ip_addr} is already in use"

            self._network.setup(
                tap_name=self._host_dev_name,
                iface_name=self._iface_name,
                gateway_ip=self._gateway_ip,
                bridge=self._bridge,
                bridge_name=self._bridge_name
            )

            self._run_firecracker()
            if not self._basic_config():
                return "Failed to configure VMM"

            self._api.actions.put(action_type="InstanceStart")

            if self._expose_ports:
                if not self._host_port or not self._dest_port:
                    raise ValueError("Port forwarding requested but no ports specified. Both host_port and dest_port must be set.")

                host_ports = [self._host_port] if isinstance(self._host_port, int) else self._host_port
                dest_ports = [self._dest_port] if isinstance(self._dest_port, int) else self._dest_port

                if len(host_ports) != len(dest_ports):
                    raise ValueError("Number of host ports must match number of destination ports")

                for host_port, dest_port in zip(host_ports, dest_ports):
                    self._network.add_port_forward(self._microvm_id, self._host_ip, host_port, self._ip_addr, dest_port)

                ports = {}
                for host_port, dest_port in zip(host_ports, dest_ports):
                    port_key = f"{dest_port}/tcp"
                    if port_key not in ports:
                        ports[port_key] = []

                    ports[port_key].append({
                        "HostPort": host_port,
                        "DestPort": dest_port
                    })
            else:
                ports = {}

            pid, create_time = self._process.get_pids(self._microvm_id)

            if self._process.is_process_running(self._microvm_id):
                self._vmm.create_vmm_json_file(
                    id=self._microvm_id,
                    Name=self._microvm_name,
                    CreatedAt=create_time,
                    Rootfs=self._rootfs_file,
                    Kernel=self._kernel_file,
                    Pid=pid,
                    Ports=ports,
                    IPAddress=self._ip_addr,
                    Labels=self._labels
                )
                return f"VMM {self._microvm_id} created"
            else:
                self._vmm.delete_vmm(self._microvm_id)
                return f"VMM {self._microvm_id} failed to create"

        except Exception as e:
            raise VMMError(f"Failed to create VMM {self._microvm_id}: {str(e)}")

        finally:
            self._api.close()

    def pause(self, id=None):
        """Pause the configured microVM.

        Args:
            id (str, optional): ID of the VMM to pause. If not provided,
                uses the current VMM's ID.

        Returns:
            str: Status message indicating the result of the pause operation.

        Raises:
            FirecrackerError: If the pause operation fails.
        """
        try:
            id = id if id else self._microvm_id
            self._vmm.update_vmm_state(id, "Paused")

            config_path = f"{self._config.data_path}/{id}/config.json"
            try:
                with open(config_path, "r+") as file:
                    config = json.load(file)
                    config['State']['Paused'] = "true"
                    file.seek(0)
                    json.dump(config, file)
                    file.truncate()
            except Exception as e:
                raise VMMError(f"Failed to update VMM state: {str(e)}")

            return f"VMM {id} paused successfully"

        except Exception as e:
            raise VMMError(str(e))

    def resume(self, id=None):
        """Resume the configured microVM.

        Args:
            id (str, optional): ID of the VMM to resume. If not provided,
                uses the current VMM's ID.

        Returns:
            str: Status message indicating the result of the resume operation.

        Raises:
            FirecrackerError: If the resume operation fails.
        """
        try:
            id = id if id else self._microvm_id
            self._vmm.update_vmm_state(id, "Resumed")

            config_path = f"{self._config.data_path}/{id}/config.json"
            try:
                with open(config_path, "r+") as file:
                    config = json.load(file)
                    config['State']['Paused'] = "false"
                    file.seek(0)
                    json.dump(config, file)
                    file.truncate()
            except Exception as e:
                raise VMMError(f"Failed to update VMM state: {str(e)}")

            return f"VMM {id} resumed successfully"

        except Exception as e:
            raise VMMError(str(e))

    def delete(self, id=None, all=False) -> str:
        """Delete a specific VMM or all VMMs and clean up associated resources.

        Args:
            id (str, optional): The ID of the VMM to delete. If not provided, the current VMM's ID is used.
            all (bool, optional): If True, delete all running VMMs. Defaults to False.

        Returns:
            str: A status message indicating the result of the deletion operation.

        Raises:
            VMMError: If an error occurs during the deletion process.
        """
        try:
            vmm_list = self._vmm.list_vmm()
            if not vmm_list:
                return "No VMMs available to delete"

            if all:
                for vmm in vmm_list:
                    self._vmm.delete_vmm(vmm['id'])
                return "All VMMs are deleted"

            target_id = id if id else self._microvm_id
            if not target_id:
                return "No VMM ID specified for deletion"

            if target_id not in [vmm['id'] for vmm in vmm_list]:
                return f"VMM with ID {target_id} not found"

            self._vmm.delete_vmm(target_id)
            return f"VMM {target_id} is deleted"

        except Exception as e:
            self._logger.error(f"Error deleting VMM: {str(e)}")
            raise VMMError(str(e))

    def connect(self, id=None, username: str = None, key_path: str = None):
        """Connect to the microVM via SSH.

        Args:
            id (str, optional): ID of the microVM to connect to. If not provided,
                uses the current VMM's ID.
            username (str, optional): SSH username. Defaults to 'root'.
            key_path (str, optional): Path to SSH private key.

        Returns:
            str: Status message indicating the SSH session was closed.

        Raises:
            VMMError: If the SSH connection fails for any reason.
        """
        if not key_path:
            return "SSH key path is required"

        if not os.path.exists(key_path):
            return f"SSH key file not found: {key_path}"

        try:
            if not self._vmm.list_vmm():
                return "No VMMs available to connect"

            id = id if id else self._microvm_id
            available_vmm_ids = [vmm['id'] for vmm in self._vmm.list_vmm()]

            if id not in available_vmm_ids:
                return f"VMM with ID {id} does not exist"

            with open(f"{self._config.data_path}/{id}/config.json", "r") as f:
                ip_addr = json.load(f)['Network'][f"tap_{id}"]['IPAddress']

            max_retries = 3
            retries = 0
            while retries < max_retries:
                try:
                    self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())
                    self._ssh_client.connect(
                        hostname=ip_addr,
                        username=username if username else self._config.ssh_user,
                        key_filename=key_path
                    )
                    break
                except paramiko.ssh_exception.NoValidConnectionsError as e:
                    retries += 1
                    if retries >= max_retries:
                        raise VMMError(
                            f"Unable to connect to the VMM {id} via SSH after {max_retries} attempts: {str(e)}"
                        )
                    time.sleep(2)

            if self._config.verbose:
                self._logger.info(f"Attempting SSH connection to {ip_addr} with user {self._config.ssh_user}")

            try:
                channel = self._ssh_client.invoke_shell()
                try:
                    old_settings = termios.tcgetattr(sys.stdin)
                    tty.setraw(sys.stdin)
                except (termios.error, AttributeError):
                    old_settings = None

                try:
                    while True:
                        if channel.exit_status_ready():
                            break

                        if channel.recv_ready():
                            data = channel.recv(1024)
                            if len(data) == 0:
                                break
                            sys.stdout.buffer.write(data)
                            sys.stdout.flush()

                        if old_settings and sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                            char = sys.stdin.read(1)
                            if not char:
                                break
                            channel.send(char)
                        elif not old_settings:
                            time.sleep(5)
                            break
                finally:
                    if old_settings:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    channel.close()
            finally:
                self._ssh_client.close()

            message = f"SSH session to VMM {id or self._microvm_id} closed"
            print(f"\n{message}\n")

        except Exception as e:
            raise VMMError(str(e))

    def port_forward(self, id=None, host_port: int = None, dest_port: int = None, remove: bool = False):
        """Forward a port from the host to the microVM and maintain the connection until interrupted.

        Args:
            host_port (int): Port on the host to forward
            dest_port (int): Port on the destination
            id (str, optional): ID of the VMM to forward ports to. If not provided, uses the last created VMM.
            remove (bool, optional): If True, remove the port forwarding rule instead of adding it.

        Raises:
            VMMError: If VMM IP address cannot be found or port forwarding fails
            ValueError: If the provided ports are not valid port numbers
        """
        try:
            if not self._vmm.list_vmm():
                return "No VMMs available to forward ports"

            id = id if id else self._microvm_id
            available_vmm_ids = [vmm['id'] for vmm in self._vmm.list_vmm()]
            if id not in available_vmm_ids:
                return f"VMM with ID {id} does not exist"

            host_ip = get_public_ip()
            if not host_ip:
                raise VMMError("Could not determine host IP address")

            config_path = f"{self._config.data_path}/{id}/config.json"
            if not os.path.exists(config_path):
                raise VMMError(f"Config file not found for VMM {id}")

            with open(config_path, "r") as f:
                config = json.load(f)
                if 'Network' not in config or f"tap_{id}" not in config['Network']:
                    raise VMMError(f"Network configuration not found for VMM {id}")
                dest_ip = config['Network'][f"tap_{id}"]['IPAddress']

            if not dest_ip:
                raise VMMError(f"Could not determine destination IP address for VMM {id}")

            if not host_port or not dest_port:
                raise ValueError("Both host_port and dest_port must be provided")

            if not isinstance(host_port, (int, list)) or not isinstance(dest_port, (int, list)):
                raise ValueError("Ports must be integers or lists of integers")

            host_ports = [host_port] if isinstance(host_port, int) else host_port
            dest_ports = [dest_port] if isinstance(dest_port, int) else dest_port

            if len(host_ports) != len(dest_ports):
                raise ValueError("Number of host ports must match number of destination ports")

            for h_port, d_port in zip(host_ports, dest_ports):
                if remove:
                    self._network.delete_port_forward(id, h_port)
                else:
                    self._network.add_port_forward(id, host_ip, h_port, dest_ip, d_port)

            return f"Port forwarding {'removed' if remove else 'added'} successfully"

        except Exception as e:
            raise VMMError(f"Failed to configure port forwarding: {str(e)}")

    def _parse_ports(self, port_value, default_value=None):
        """Parse port values from various input formats.

        Args:
            port_value: Port specification that could be None, an integer, a string with comma-separated values,
                    or a list of integers
            default_value: Default value to use if port_value is None

        Returns:
            list: A list of integer port values
        """
        if port_value is None:
            return [default_value] if default_value is not None else []

        if isinstance(port_value, int):
            return [port_value]

        if isinstance(port_value, str):
            if ',' in port_value:
                return [int(p.strip()) for p in port_value.split(',') if p.strip().isdigit()]
            elif port_value.isdigit():
                return [int(port_value)]

        if isinstance(port_value, list):
            ports = []
            for p in port_value:
                if isinstance(p, int):
                    ports.append(p)
                elif isinstance(p, str) and p.isdigit():
                    ports.append(int(p))
            return ports

        return []

    def _basic_config(self) -> bool:
        """Configure the microVM with basic settings.

        This method orchestrates the configuration of various components:
        - Boot source
        - Root drive
        - Machine resources (vCPUs and memory)
        - Network interface
        - MMDS (if enabled)

        Returns:
            bool: True if configuration is successful, False otherwise.
        """
        try:
            self._configure_vmm_boot_source()
            self._configure_vmm_root_drive()
            self._configure_vmm_resources()
            self._configure_vmm_network()
            if self._mmds_enabled:
                self._configure_vmm_mmds()
            return True
        except Exception as exc:
            raise ConfigurationError(str(exc))

    @property
    def _boot_args(self):
        """Generate boot arguments using current configuration."""
        common_args = (
            "console=ttyS0 reboot=k panic=1 "
            f"ip={self._ip_addr}::{self._gateway_ip}:255.255.255.0:"
            f"{self._microvm_name}:{self._iface_name}:on"
        )

        if self._mmds_enabled:
            return f"{common_args} init={self._init_file}"
        elif self._overlayfs:
            return f"{common_args} init={self._init_file} overlay_root=/vdb"
        else:
            return f"{common_args}"

    def _configure_vmm_boot_source(self):
        """Configure the boot source for the microVM."""
        try:
            if not os.path.exists(self._kernel_file):
                raise ConfigurationError(f"Kernel file not found: {self._kernel_file}")

            boot_params = {
                'kernel_image_path': self._kernel_file,
                'boot_args': self._boot_args
            }

            if self._initrd_file:
                boot_params['initrd_path'] = self._initrd_file
                self._logger.info(f"Using initrd file: {self._initrd_file}")

            boot_response = self._api.boot.put(**boot_params)

            if self._config.verbose:
                self._logger.debug(f"Boot configuration response: {boot_response.status_code}")
                self._logger.info("Boot source configured")

        except Exception as e:
            raise ConfigurationError(f"Failed to configure boot source: {str(e)}")

    def _configure_vmm_root_drive(self):
        """Configure the root drive for the microVM."""
        try:
            self._api.drive.put(
                drive_id="rootfs",
                path_on_host=self._rootfs_file if not self._overlayfs else self._base_rootfs,
                is_root_device=True,
                is_read_only=self._overlayfs is True
            )
            if self._config.verbose:
                self._logger.info("Root drive configured")

            if self._overlayfs:
                self._api.drive.put(
                    drive_id="overlayfs",
                    path_on_host=self._overlayfs_file,
                    is_root_device=False,
                    is_read_only=False
                )

                if self._config.verbose:
                    self._logger.info("Overlayfs drive configured")

        except Exception:
            raise ConfigurationError("Failed to configure root drive")

    def _configure_vmm_resources(self):
        """Configure machine resources (vCPUs and memory)."""
        try:
            self._api.machine_config.put(
                vcpu_count=self._vcpu,
                mem_size_mib=self._memory
            )

            if self._config.verbose:
                self._logger.info(f"Configured VMM with {self._vcpu} vCPUs and {self._memory} MiB RAM")

        except Exception as e:
            raise ConfigurationError(f"Failed to configure VMM resources: {str(e)}")

    def _configure_vmm_network(self):
        """Configure network interface.

        Raises:
            NetworkError: If network configuration fails
        """
        try:
            response = self._api.network.put(
                iface_id=self._iface_name,
                guest_mac=self._mac_addr,
                host_dev_name=self._host_dev_name
            )

            if self._config.verbose:
                self._logger.debug(f"Network configuration response: {response.status_code}")
                self._logger.info("Configured network interface")

        except Exception as e:
            raise ConfigurationError(f"Failed to configure network: {str(e)}")

    def _configure_vmm_mmds(self):
        """Configure MMDS (Microvm Metadata Service) if enabled.

        MMDS is a service that provides metadata to the microVM.
        """
        try:
            if self._config.verbose:
                self._logger.info("MMDS is " + ("disabled" if not self._mmds_enabled else "enabled, configuring MMDS network..."))

            if not self._mmds_enabled:
                return

            self._api.mmds_config.put(
                version="V2",
                ipv4_address=self._mmds_ip,
                network_interfaces=[self._iface_name]
            )

            user_data = {
                "latest": {
                    "meta-data": {
                        "instance-id": self._microvm_id,
                        "local-hostname": self._microvm_name
                    }
                }
            }

            if self._user_data:
                user_data["latest"]["user-data"] = self._user_data
                if hasattr(self, '_user_data_file') and self._user_data_file:
                    user_data["latest"]["meta-data"]["user-data-file"] = self._user_data_file

            mmds_data_response = self._api.mmds.put(**user_data)

            if self._config.verbose:
                self._logger.debug(f"MMDS data response: {mmds_data_response.status_code}")
                self._logger.info("MMDS data configured")

        except Exception as e:
            raise ConfigurationError(f"Failed to configure MMDS: {str(e)}")

    def _run_firecracker(self) -> Tuple[Api, int]:
        """Start a new Firecracker process using screen."""
        try:
            self._vmm._ensure_socket_file(self._microvm_id)

            paths = [self._vmm_dir, f"{self._vmm_dir}/rootfs", f"{self._vmm_dir}/logs"]
            for path in paths:
                self._vmm.create_vmm_dir(path)

            if not self._overlayfs:
                run(f"cp {self._base_rootfs} {self._rootfs_file}")
                if self._config.verbose:
                    self._logger.debug(f"Copied base rootfs from {self._base_rootfs} to {self._rootfs_file}")

            for log_file in [f"{self._microvm_id}.log", f"{self._microvm_id}_screen.log"]:
                self._vmm.create_log_file(self._microvm_id, log_file)

            binary_params = [
                f"--api-sock {self._socket_file}",
                f"--id {self._microvm_id}",
                f"--log-path {self._log_dir}/{self._microvm_id}.log"
            ]

            session_name = f"fc_{self._microvm_id}"
            screen_pid = self._process.start_screen_process(
                screen_log=f"{self._log_dir}/{self._microvm_id}_screen.log",
                session_name=session_name,
                binary_path=self._config.binary_path,
                binary_params=binary_params
            )
            
            if not psutil.pid_exists(int(screen_pid)):
                raise ProcessError("Firecracker process is not running")

            for _ in range(3):
                try:
                    response = self._api.describe.get()
                    if response.status_code == HTTPStatus.OK:
                        return Api(self._socket_file)
                except Exception:
                    pass
                time.sleep(0.5)

            raise APIError(f"Error {response.status_code}: Failed to connect to the API socket")

        except Exception as exc:
            self._vmm.cleanup(self._microvm_id)
            raise VMMError(str(exc))

    def _download_rootfs(self, url: str):
        """Download the rootfs from the given URL."""

        if not url.startswith(("http://", "https://")):
            raise VMMError(f"Invalid URL: {url}")

        try:
            with closing(requests.get(url, stream=True, timeout=10)) as response:
                response.raise_for_status()

                if self._config.verbose:
                    self._logger.info(f"Downloading rootfs from {url}")

                filename = url.split("/")[-1]
                path = os.path.join(self._config.data_path, filename)

                with open(path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                return path

        except Exception as e:
            raise VMMError(f"Failed to download rootfs from {url}: {str(e)}")

    def _convert_memory_size(self, size):
        """Convert memory size to MiB.
        
        Args:
            size: Memory size in format like '1G', '2G', or plain number (assumed to be MiB)
            
        Returns:
            int: Memory size in MiB
        """
        MIN_MEMORY = 128  # Minimum memory size in MiB
        
        if isinstance(size, int):
            return max(size, MIN_MEMORY)
            
        if isinstance(size, str):
            size = size.upper().strip()
            try:
                if size.endswith('G'):
                    # Convert GB to MiB and ensure minimum
                    mem_size = int(float(size[:-1]) * 1024)
                elif size.endswith('M'):
                    # Already in MiB, just convert
                    mem_size = int(float(size[:-1]))
                else:
                    # If no unit specified, assume MiB
                    mem_size = int(float(size))
                
                return max(mem_size, MIN_MEMORY)
            except ValueError:
                raise ValueError(f"Invalid memory size format: {size}")
        raise ValueError(f"Invalid memory size type: {type(size)}")
