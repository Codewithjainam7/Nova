from backend.capabilities.schema import CapabilityDescriptor

DEFAULT_CAPABILITIES = [
    CapabilityDescriptor(
        capability_id="cap_launch_application",
        name="LaunchApplication",
        description="Launch an application on the user's OS",
        categories=["os", "desktop"],
        dependencies=[]
    ),
    CapabilityDescriptor(
        capability_id="cap_manage_windows",
        name="ManageWindows",
        description="Manage GUI windows",
        categories=["os", "desktop"],
        dependencies=[]
    ),
    CapabilityDescriptor(
        capability_id="cap_filesystem",
        name="Filesystem",
        description="Read/write files on the local filesystem",
        categories=["os", "filesystem"],
        dependencies=[]
    ),
    CapabilityDescriptor(
        capability_id="cap_clipboard",
        name="Clipboard",
        description="Access and manipulate the system clipboard",
        categories=["os", "clipboard"],
        dependencies=[]
    ),
    CapabilityDescriptor(
        capability_id="cap_browser_navigation",
        name="BrowserNavigation",
        description="Navigate webpages in a browser",
        categories=["web", "browser"],
        dependencies=[]
    ),
    CapabilityDescriptor(
        capability_id="cap_internet_search",
        name="InternetSearch",
        description="Perform internet searches",
        categories=["web", "search"],
        dependencies=[]
    ),
    CapabilityDescriptor(
        capability_id="cap_email_management",
        name="EmailManagement",
        description="Send and read emails",
        categories=["communication", "email"],
        dependencies=[]
    )
]
