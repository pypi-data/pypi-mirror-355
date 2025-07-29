# pf-reasoning-tool-proj/setup.py

from setuptools import setup, find_packages

# --- List of all required packages for ALL your tools ---
# This ensures that when you pip install your tool package, all necessary libraries are also installed.
INSTALL_REQUIRES = [
    "promptflow>=1.10.0",
    "promptflow-tools>=1.5.0",
    "ruamel.yaml>=0.17",
    "openai>=1.10",
    # Pinning specific, stable versions is best practice for reproducibility
    "azure-ai-textanalytics==5.3.0",
    "azure-search-documents==11.4.0",
    "azure-identity", # A common peer dependency for Azure SDKs
]

setup(
    name="pf_reasoning_tool",
    version="0.5.13",  # <-- Incremented version to ensure a fresh install
    packages=find_packages(),
    description="A collection of custom PromptFlow tools for Hall & Wilcox.",

    # This tells pip to install the packages listed above
    install_requires=INSTALL_REQUIRES,

    # This includes your YAML files in the package. It's more explicit than just using MANIFEST.in.
    include_package_data=True,
    package_data={
        'pf_reasoning_tool': ['yamls/*.yaml', 'tools/icons/*'],
    },

    # --- CRITICAL FIX ---
    # This is the correct entry point group for PromptFlow to discover your tools.
    entry_points={
        "package_tools": [
            # utils.py dynamically discovers every YAML in pf_reasoning_tool/yamls
            "pf_reasoning_tool = pf_reasoning_tool.tools.utils:list_package_tools",
        ]
    },
)