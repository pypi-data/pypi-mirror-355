try:
    from http_prober.modules.cli.cli import CommandLine
    from http_prober.modules.prober.prober import HttpProber
    from http_prober.modules.utils.utils import read_from_file

except ImportError as Ie:
    print(f"[ + ] Import Error [modules.core]: {Ie}")
    exit(1)


class HttpProberCore:
    """
        Class to handle the http prober.

        Args:
            verbose (bool):  To enable verbose mode. 

        Retruns:
            None. 
    """
    def __init__(self,verbose:bool = False) -> None:
        self.verbose = verbose
        self.default_semaphore_count = 100
        self.commandline = CommandLine()

    def main(self) -> None:
        """
            Main function for the Http-Prober handler.

            Args:
                None. 

            Retruns:
                None. 
        """
        # Prining HttpProber's banner. 
        print(self.commandline.get_banner())

        arguments = self.commandline.get_arguments()

        if arguments.help:
            print(self.commandline.get_help())
            exit()

        if arguments.url and arguments.url_list:
            print("Usage: http-prober ( -u / --url-list ) [options] \nDuplicate Input entry, Use --help to see more options.")
            exit(1)
        
        else:
            # Checking the input arguments has both url and url list exist. 
            if arguments.url or arguments.url_list:
                if arguments.verbose:
                    self.verbose = True
                    print(f"[ + ] Verbose mode enabled.")

                urls = []
                semaphore_count = arguments.concurrency if arguments.concurrency else self.default_semaphore_count
                
                if semaphore_count != self.default_semaphore_count:
                    print(f"[ + ] Semaphore Count configured to {semaphore_count}")

                prober = HttpProber(verbose = self.verbose ,semaphore_count = semaphore_count)
                
                # Block for singlt url.
                if arguments.url: 
                    urls.append(str(arguments.url))

                    if self.verbose:
                        print(f"[ + ] Total urls to check: {len(urls)}.")

                # Block for url list.
                elif arguments.url_list:
                    contents = read_from_file(arguments.url_list)

                    if contents:
                        urls.extend(contents)

                    if self.verbose:
                        print(f"[ + ] Total urls to check: {len(urls)}")
                
                print(f"[ + ] Http Prober started !!")

                # Starting the http prober with urls.
                prober_result = prober.run(urls)

                # printing enumerated results.
                if prober_result:
                    print(f"\n[ + ] Result:")
                    for result in prober_result:
                        print(f"      {result["url"]} [{result["status"]}]")

                else:
                    print(f"[ ! ] Something went wrong,try again")
                    exit(1)

            else:
                print("Usage: http-prober ( -u / --url-list ) [options] \nUse --help to see more options.")
                exit(1)

    def run(self) -> None:
        """
            Function to run the Http-Prober.

            Args:
                None
            
            Returns:
                None
        """
        
        self.main()

def start():
    http_prober = HttpProberCore()
    http_prober.run()