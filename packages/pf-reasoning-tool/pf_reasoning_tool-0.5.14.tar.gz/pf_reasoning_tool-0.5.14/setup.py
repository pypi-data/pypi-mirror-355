# pf-reasoning-tool-proj/setup.py

from setuptools import find_packages, setup

PACKAGE_NAME = "pf_reasoning_tool"

# --- List of all required packages for ALL your tools ---
# This ensures that when you pip install your tool package, all necessary libraries are also installed.
INSTALL_REQUIRES = [
    "promptflow-tools>=1.5.0",
    "ruamel.yaml>=0.17",  # For your utils.py to load YAMLs
    "openai>=1.10.0",  # For reasoning_tool, vision_tool, etc.
    "azure-ai-textanalytics==5.3.0",    # For the PII redaction tool
    "azure-search-documents==11.4.0",   # For the AI Search tool (using stable, not beta)
    "azure-identity",                   # A common peer dependency for Azure SDKs
]

setup(
    name=PACKAGE_NAME,
    version="0.5.14",  # <-- IMPORTANT: Incremented version for a clean update
    description="Custom PromptFlow tools for Hall & Wilcox",
    packages=find_packages(),
    
    # This is the correct entry point for the 'pf tool build' workflow
    entry_points={
        "package_tools": [
            "pf_reasoning_tool = pf_reasoning_tool.tools.utils:list_package_tools",
        ],
    },
    
    # This tells pip to install the packages listed above
    install_requires=INSTALL_REQUIRES,

    # This tells setuptools to include non-Python files specified in MANIFEST.in
    include_package_data=True,
)