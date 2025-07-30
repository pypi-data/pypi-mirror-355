try:
    import argparse
    from colorama import Fore,Style

except ImportError as Ie:
    print(f"[ + ] Import Error [modules.cli]: {Ie}'")

class CommandLine:
    """
        Class to handle commandline.

        Args:
            None
        
        Results:
            None
    """
    def __init__(self) -> None:
        self.blue = Fore.BLUE
        self.red = Fore.RED
        self.blue = Fore.BLUE
        self.white = Fore.WHITE
        self.magenta = Fore.MAGENTA
        self.bright = Style.BRIGHT
        self.green = Fore.GREEN
        self.red = Fore.RED
        self.bold = Style.BRIGHT
        self.reset = Style.RESET_ALL

    def get_banner(self) ->str:
        """
            Function that return banner for the Http-Prober.

            Args:
                None
            
            Returns:
                Banner (str) : Banner for the Http-Prober.
                
        """
        banner = f"""{self.red}
        
          ___ ___   __    __                  __________              ___.                 
         /   |   \\_/  |__/  |_______          \\______   \\_______  ____\\_ |__   ___________ 
        /    ~    \\   __\\   __\\____ \\   ______ |     ___/\\_  __ \\/  _ \\| __ \\_/ __ \\_  __ \\
        \\    Y    /|  |  |  | |  |_> > /_____/ |    |     |  | \\(  <_> ) \\_\\ \\  ___/|  | \\/
         \\___|_  / |__|  |__| |   __/          |____|     |__|   \\____/|___  /\\___  >__|   
               \\/             |__|                                         \\/     \\/       
                                                   

                {self.reset}        Async probing tool to enumerate status code using aiohttp.
                                          Github : {self.green}pevinkumar10{self.reset}
        """

        return banner

    def get_arguments(self) -> list:
        """
            Function to parse arguments.

            Args:
                None
            
            Returns:
                Arguments for the Http-Prober.

        """
        parser = argparse.ArgumentParser(add_help = False,usage = argparse.SUPPRESS,exit_on_error = False)
        try:
            parser.add_argument("-u","--url",type=str)
            parser.add_argument("-uL","--url-list")
            parser.add_argument("-c","--concurrency",type=int)
            parser.add_argument("-v","--verbose",action="store_true")
            parser.add_argument("-h","--help",action="store_true")

            arguments = parser.parse_args()

            return arguments
        
        except argparse.ArgumentError:
            print(f"{self.bright}{self.red}[ ! ] {self.reset}{self.blue}Value Error ,Please use -h to get more information.")
            exit()
            
        except argparse.ArgumentTypeError:
            print(f"{self.bright}{self.blue}\n [ ! ] {self.reset}{self.blue}Please use -h to get more information.")
            exit()
        
        except Exception as e:
            print(f"{self.bright}{self.red}\n [ ! ] {self.reset}{self.blue}Unexpected Argument Error:{e}")
            exit()
    
    def get_help(self) ->str:
        """
            Function that return Help menu for the Http-Prober.

            Args:
                None
            
            Returns:
                Help menu (str) : Help menu for the Http-Prober.
                
        """
        return f"""
        {self.bold}{self.white}[{self.reset}{self.bold}{self.blue}DESCRIPTION{self.reset}{self.white}]{self.reset}: {self.white}{self.bold}http-prober{self.reset} {self.white}is a tool used to enumerate status code from the given url(s) by{self.reset}{self.bold}{self.green} Pevinkumar A{self.reset}.\n
            {self.bold}{self.white}[{self.reset}{self.bold}{self.blue}Usage{self.reset}{self.white}]{self.reset}: http-prober [ options ]\n
                    {self.white}http-prober {self.bold}{self.white}<{self.reset}{self.bold}{self.blue}Flags{self.reset}{self.bold}{self.white}>\n
            [{self.reset}{self.bold}{self.blue}Flags{self.reset}{self.bold}{self.white}]
                    [{self.reset}{self.bold}{self.blue}Input{self.reset}{self.bold}{self.white}]{self.reset}
                        -u,   --url                     :  Url to check status code.                                                
                        -uL,  --url-list                :  List of urls to scan status code.  

                    [{self.reset}{self.bold}{self.blue}Options{self.reset}{self.bold}{self.white}]{self.reset}
                        -c,   --concurrency             :  Number of concurrency allowed to run simultaniously (default : 100)               

                    {self.bold}{self.white}[{self.reset}{self.bold}{self.blue}Debug{self.reset}{self.bold}{self.white}]{self.reset}
                        -v,   --verbose                 :  To set verbose mode flag for more detailed output.
                        -h,   --help                    :  To see all the available options.

                        """
    