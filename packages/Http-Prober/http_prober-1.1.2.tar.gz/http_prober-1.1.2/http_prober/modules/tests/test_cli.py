try:
    from http_prober.modules.cli.cli import CommandLine
    from colorama import Fore,Style

except ImportError as Ie:
    print(f"[ + ] Import Error [modules.tests.cli]: {Ie}")

# Intializing the CommandLine class to test.
cli = CommandLine()

blue = Fore.BLUE
red = Fore.RED
blue = Fore.BLUE
white = Fore.WHITE
magenta = Fore.MAGENTA
bright = Style.BRIGHT
green = Fore.GREEN
red = Fore.RED
bold = Style.BRIGHT
reset = Style.RESET_ALL

def test_banner() -> bool:
    """
        Function to test the get_banner in CommandLine class with expected result. 

        Args:
            None
            
        Returns:
            bool    :   Returns True if expected result match with test result.
                
    """
    banner = cli.get_banner()
    expected = f"""{red}
        
          ___ ___   __    __                  __________              ___.                 
         /   |   \\_/  |__/  |_______          \\______   \\_______  ____\\_ |__   ___________ 
        /    ~    \\   __\\   __\\____ \\   ______ |     ___/\\_  __ \\/  _ \\| __ \\_/ __ \\_  __ \\
        \\    Y    /|  |  |  | |  |_> > /_____/ |    |     |  | \\(  <_> ) \\_\\ \\  ___/|  | \\/
         \\___|_  / |__|  |__| |   __/          |____|     |__|   \\____/|___  /\\___  >__|   
               \\/             |__|                                         \\/     \\/       
                                                   

                {reset}        Async probing tool to enumerate status code using aiohttp.
                                          Github : {green}pevinkumar10{reset}
        """

    assert banner.strip() == expected.strip()


def test_helpmenu() -> bool:
    """
        Function to test the get_help_menu in CommandLine class with expected result. 

        Args:
            None
            
        Returns:
            bool    :   Returns True if expected result match with test result.
                
    """
    help_menu = cli.get_help()
    expected = f"""
        {bold}{white}[{reset}{bold}{blue}DESCRIPTION{reset}{white}]{reset}: {white}{bold}http-prober{reset} {white}is a tool used to enumerate status code from the given url(s) by{reset}{bold}{green} Pevinkumar A{reset}.\n
            {bold}{white}[{reset}{bold}{blue}Usage{reset}{white}]{reset}: http-prober [ options ]\n
                    {white}http-prober {bold}{white}<{reset}{bold}{blue}Flags{reset}{bold}{white}>\n
            [{reset}{bold}{blue}Flags{reset}{bold}{white}]
                    [{reset}{bold}{blue}Input{reset}{bold}{white}]{reset}
                        -u,   --url                     :  Url to check status code.                                                
                        -uL,  --url-list                :  List of urls to scan status code.  

                    [{reset}{bold}{blue}Options{reset}{bold}{white}]{reset}
                        -c,   --concurrency             :  Number of concurrency allowed to run simultaniously (default : 100)               

                    {bold}{white}[{reset}{bold}{blue}Debug{reset}{bold}{white}]{reset}
                        -v,   --verbose                 :  To set verbose mode flag for more detailed output.
                        -h,   --help                    :  To see all the available options.

            """
    assert help_menu.strip() == expected.strip()

