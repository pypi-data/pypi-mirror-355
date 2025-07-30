import random
import socket
from rich.text import Text
from rich.console import Console

banner = """
██████╗ ██████╗  ██████╗ ██╗    ██╗███████╗███████╗██████╗             
██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔════╝██╔══██╗            
██████╔╝██████╔╝██║   ██║██║ █╗ ██║███████╗█████╗  ██████╔╝            
██╔══██╗██╔══██╗██║   ██║██║███╗██║╚════██║██╔══╝  ██╔══██╗            
██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝███████║███████╗██║  ██║            
╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝  ╚═╝            

██╗  ██╗██╗███████╗████████╗ ██████╗ ██████╗ ██╗   ██╗                 
██║  ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝                 
███████║██║███████╗   ██║   ██║   ██║██████╔╝ ╚████╔╝                  
██╔══██║██║╚════██║   ██║   ██║   ██║██╔══██╗  ╚██╔╝                   
██║  ██║██║███████║   ██║   ╚██████╔╝██║  ██║   ██║                   
╚═╝  ╚═╝╚═╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝                   

 █████╗ ███╗   ██╗ █████╗ ██╗     ██╗   ██╗████████╗██╗ ██████╗███████╗
██╔══██╗████╗  ██║██╔══██╗██║     ╚██╗ ██╔╝╚══██╔══╝██║██╔════╝██╔════╝
███████║██╔██╗ ██║███████║██║      ╚████╔╝    ██║   ██║██║     ███████╗
██╔══██║██║╚██╗██║██╔══██║██║       ╚██╔╝     ██║   ██║██║     ╚════██║
██║  ██║██║ ╚████║██║  ██║███████╗   ██║      ██║   ██║╚██████╗███████║
╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝   ╚═╝      ╚═╝   ╚═╝ ╚═════╝╚══════╝
"""

console = Console()

PORT = "2907"
rainbow_colors = [
    "dark_cyan",
    "light_sea_green",
    "deep_sky_blue2",
    "deep_sky_blue1",
    "green3",
    "spring_green3",
    "cyan3",
    "dark_turquoise",
    "turquoise2"
]

def fetch_network_ip():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return f"Network URL: http://{ip_address}:{PORT}\n"
    except socket.error as e:
        console.print(f"Error fetching network IP: {e}", style="bold red")
        return ""

def print_content():
    for line in banner.strip("\n").splitlines():
        text_line = Text()
        for ch in line:
            color = random.choice(rainbow_colors)
            text_line.append(ch, style=f"bold {color}")
        console.print(text_line)
        
    console.print("\n")
    console.print(
        "Welcome to Browser History Analytics! "
        "This tool helps you analyze your browser history data. "
        "You can now view your visualizations in your browser.\n"
    )
    console.print(
        f"Local URL: http://localhost:{PORT}\n"
        f"{fetch_network_ip()}",
        style="bold cyan1")