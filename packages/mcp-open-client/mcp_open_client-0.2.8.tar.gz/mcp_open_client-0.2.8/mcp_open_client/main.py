from nicegui import ui, app
import asyncio
import json
import sys

# Import UI components
from mcp_open_client.ui.home import show_content as show_home_content
from mcp_open_client.ui.mcp_servers import show_content as show_mcp_servers_content
from mcp_open_client.ui.configure import show_content as show_configure_content
from mcp_open_client.ui.chat_window import show_content as show_chat_content

# Import MCP client manager
from mcp_open_client.mcp_client import mcp_client_manager

# Load the external CSS file from settings directory with cache busting
ui.add_css(f'mcp_open_client/settings/app-styles.css?v={__import__("time").time()}')

def init_storage():
    """Initialize storage without JavaScript execution"""
    # Initialize user settings
    if 'user-settings' not in app.storage.user:
        app.storage.user['user-settings'] = {"clave": "valor"}
    
    # Initialize theme from browser storage or default to dark
    if 'dark_mode' not in app.storage.browser:
        app.storage.browser['dark_mode'] = True
    ui.dark_mode().bind_value(app.storage.browser, 'dark_mode')
    
    # Always load configuration from file to ensure persistence
    try:
        with open('mcp_open_client/settings/mcp-config.json', 'r') as f:
            app.storage.user['mcp-config'] = json.load(f)
        print("Loaded MCP configuration from file")
    except Exception as e:
        print(f"Error loading MCP configuration: {str(e)}")
        # Only initialize empty config if it doesn't exist in storage
        if 'mcp-config' not in app.storage.user:
            app.storage.user['mcp-config'] = {"mcpServers": {}}

async def init_mcp_client():
    """Initialize MCP client manager with the configuration"""
    # Add a flag to prevent multiple initializations
    if not hasattr(app.storage.user, 'mcp_initializing') or not app.storage.user.mcp_initializing:
        app.storage.user.mcp_initializing = True
        try:
            config = app.storage.user.get('mcp-config', {})
            success = await mcp_client_manager.initialize(config)
            
            # We need to use a safe way to notify from background tasks
            if success:
                active_servers = mcp_client_manager.get_active_servers()
                server_count = len(active_servers)
                # Use app.storage to communicate with the UI
                app.storage.user['mcp_status'] = f"Connected to {server_count} MCP servers"
                app.storage.user['mcp_status_color'] = 'positive'
            else:
                app.storage.user['mcp_status'] = "No active MCP servers found"
                app.storage.user['mcp_status_color'] = 'warning'
        finally:
            app.storage.user.mcp_initializing = False



def setup_ui():
    """Setup the UI components"""
    @ui.page('/')
    def index():
        """Main application page"""
        
        # Initialize storage first
        init_storage()
        
        # Run the MCP initialization asynchronously
        asyncio.create_task(init_mcp_client())
        
        # Create a status indicator that updates from storage
        last_status = {'message': None, 'color': None}
        
        def update_status():
            nonlocal last_status
            if 'mcp_status' in app.storage.user:
                status = app.storage.user['mcp_status']
                color = app.storage.user.get('mcp_status_color', 'info')
                
                # Only show notification if status has changed
                if status != last_status['message'] or color != last_status['color']:
                    ui.notify(status, color=color)
                    last_status['message'] = status
                    last_status['color'] = color
        
        # Check for status updates periodically
        ui.timer(1.0, update_status)
        
        # Variable local para sección activa (NO usar storage para esto)
        active_section = 'home'
        
        # Función para verificar si una sección está activa
        def is_active(section):
            return 'active' if section == active_section else ''
        
        content_container = ui.row().classes('h-full w-full')
        
        def update_content(section):
            nonlocal active_section
            active_section = section  # ✅ Variable local, NO storage
            # Actualizar las clases de los elementos del menú
            for item in left_drawer.default_slot.children:
                if hasattr(item, 'default_slot') and item.default_slot.children:
                    for child in item.default_slot.children:
                        if hasattr(child, 'classes'):
                            section_name = child.props.get('on_click', lambda: None).__name__.split('_')[-1]
                            if section_name == section:
                                child.classes(add='active')
                            else:
                                child.classes(remove='active')
            content_container.clear()
            
            if section == 'home':
                show_home_content(content_container)
            elif section == 'mcp_servers':
                show_mcp_servers_content(content_container)
            elif section == 'configure':
                show_configure_content(content_container)
            elif section == 'chat':
                show_chat_content(content_container)
        
        with ui.header(elevated=True).classes('app-header'):
            with ui.row().classes('items-center full-width'):
                with ui.row().classes('items-center'):
                    ui.button(on_click=lambda: left_drawer.toggle(), icon='menu').classes('q-mr-sm')
                    ui.label('MCP-Open-Client').classes('app-title text-h5')
                
                ui.space()
                
                with ui.row().classes('items-center'):
                    ui.button(icon='notifications').classes('q-mr-sm').tooltip('Notifications')
                    ui.button(icon='help_outline').classes('q-mr-sm').tooltip('Help')
                    ui.button(icon='dark_mode', on_click=lambda: ui.dark_mode().toggle()).classes('q-mr-sm').tooltip('Toggle dark/light mode')
                    ui.button(icon='account_circle').tooltip('User Account')
        
        with ui.left_drawer(top_corner=True, bottom_corner=True).classes('nav-drawer q-pa-md') as left_drawer:
            ui.label('Navigation Menu').classes('text-h6 nav-title q-mb-lg')
            
            with ui.column().classes('w-full gap-2'):
                # Home button
                ui.button(
                    'Home',
                    icon='home',
                    on_click=lambda: update_content('home')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("home")}'
                )
                # MCP Servers button
                ui.button(
                    'MCP Servers',
                    icon='dns',
                    on_click=lambda: update_content('mcp_servers')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("mcp_servers")}'
                )
                
                # Configure button
                ui.button(
                    'Configure',
                    icon='settings',
                    on_click=lambda: update_content('configure')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("configure")}'
                )
                
                # Chat button
                ui.button(
                    'Chat',
                    icon='chat',
                    on_click=lambda: update_content('chat')
                ).props(
                    'flat no-caps align-left full-width'
                ).classes(
                    f'drawer-btn text-weight-medium text-subtitle1 q-py-sm {is_active("chat")}'
                )
            
            ui.separator()
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('© 2025 MCP Open Client').classes('text-subtitle2')
                with ui.row().classes('items-center'):
                    ui.button('Documentation', on_click=lambda: ui.open('https://docs.mcp-open-client.com'))
        
        # Set home as the default content
        update_content('chat')

def main():
    """Main entry point"""
    setup_ui()

def cli_entry():
    """Entry point for console script"""
    setup_ui()

# Setup UI when module is imported
setup_ui()

# Run the server - this needs to be at module level for entry points
ui.run(
    storage_secret="ultrasecretkeyboard",
    port=8081,
    reload=True,
    dark=True,
    show_welcome_message=True,
    show=False
)