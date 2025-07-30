__version__ = "0.0.2"

import os
import tempfile
import importlib.util
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

def load_encrypted_module(module_name, file_path, key):
    print(f"Attempting to decrypt {file_path} as {module_name}")
    cipher = Fernet(key)
    try:
        with open(file_path, 'rb') as f:
            encrypted = f.read()
        print(f"Read {len(encrypted)} bytes from {file_path}")
        decrypted = cipher.decrypt(encrypted)
        print(f"Decrypted {len(decrypted)} bytes for {module_name}")
        with tempfile.NamedTemporaryFile(suffix='.so', delete=False) as tmp:
            tmp.write(decrypted)
            tmp_path = tmp.name
        spec = importlib.util.spec_from_file_location(module_name, tmp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        os.remove(tmp_path)
        print(f"Successfully loaded {module_name}")
        return module
    except Exception as e:
        print(f"Failed to decrypt/load {module_name}: {type(e).__name__}: {str(e)}")
        raise

# Load encrypted modules in dependency order
license_key = None
modules_to_load = []
dependency_order = [
    "agentfoundry.registry.tool_registry",
    "agentfoundry.registry.database",
    "agentfoundry.utils.logger",
    "agentfoundry.utils.config",
    "agentfoundry.utils.exceptions",
    "agentfoundry.agents.base_agent",
    # Add other critical dependencies here
]

# Collect all .so files
for root, _, files in os.walk(os.path.dirname(__file__)):
    for file in files:
        if file.endswith('.so') and not file.endswith('.so.enc'):
            rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(__file__))
            module_name = rel_path.replace(os.sep, '.')[:-len('.cpython-311-x86_64-linux-gnu.so')]
            module_path = os.path.join(root, file)
            modules_to_load.append((module_name, module_path))

# Sort modules to prioritize dependencies
modules_to_load.sort(key=lambda x: (0 if x[0] in dependency_order else 1, dependency_order.index(x[0]) if x[0] in dependency_order else len(dependency_order)))

for module_name, module_path in modules_to_load:
    if license_key is None:
        print("Retrieving decryption key...")
        try:
            with open(os.path.join(os.path.dirname(__file__), "agentfoundry.lic"), 'r') as f:
                license_data = json.load(f)
            with open(os.path.join(os.path.dirname(__file__), "agentfoundry.pem"), 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())
            signature = base64.b64decode(license_data['signature'])
            license_content = json.dumps(license_data['content'], sort_keys=True).encode()
            public_key.verify(
                signature,
                license_content,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            license_key = base64.b64decode(license_data['content']['decryption_key'])
            print(f"Decryption key: {license_key}")
        except Exception as e:
            print(f"Failed to retrieve decryption key: {type(e).__name__}: {str(e)}")
            raise RuntimeError("Failed to retrieve decryption key")
    try:
        module = load_encrypted_module(module_name, module_path, license_key)
        globals()[module_name] = module
    except Exception as e:
        print(f"Failed to process {module_name}: {type(e).__name__}: {str(e)}")

# Import modules after decryption
from .registry.tool_registry import ToolRegistry
from .agents.base_agent import BaseAgent
from .agents.orchestrator import Orchestrator
from .agents.tool_autonomy_agent import ToolAutonomyAgent
from .license.license import enforce_license, verify_license
from .license.key_manager import get_license_key

__all__ = [
    "ToolRegistry",
    "BaseAgent",
    "Orchestrator",
    "ToolAutonomyAgent",
    "enforce_license",
    "get_license_key",
]