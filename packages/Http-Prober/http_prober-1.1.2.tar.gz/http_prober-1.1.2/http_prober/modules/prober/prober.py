try:
    import asyncio
    import httpx
    from colorama import Fore,Style
    from time import perf_counter

except ImportError as Ie:
    print(f"[ + ] Import Error [modules.prober]: {Ie}'")
    exit(1)

class HttpProber:
    """
        Class to probe the http status code from url(s) using asynchronous programming.

        Args:
            semaphore_count (int):  To specify the maximum number of tasks to run simultaniously ( default 100 ).
            timeout (int):   To specify the maximum waiting time for a task.
            verbose (bool):  To enable verbose mode. 

        Retruns:
            list: It returns the list for urls with statuscodes. 
    """
    def __init__(self,semaphore_count:int, timeout:int = 5,verbose:bool = False) -> None:
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

        self.timeout = timeout
        self.verbose = verbose
        self.semaphore = asyncio.Semaphore(semaphore_count)

    async def make_request(self,url:str,timeout:int,client_session:object) -> None:
        """
            Async coroutine to make a request to the given url.

            Args:
                url (str)   : Url to make to check status code.
                client_session  (object):   The client session object which is used to make request to the url.

            Returns:
                None
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HttpProber/1.0.0;)"
        }

        max_retry = 2
        retry_delay = 3

        async with self.semaphore:
            failed_reason = ""
            for attempt in range(1,max_retry+1):
                try:
                    # Checking the url.
                    if url.startswith("http://") or url.startswith("https://"):
                        pass
                    else:
                        url = "https://" + url
                        
                    # Making get request to the url.
                    response = await client_session.get(url ,headers = headers ,timeout = timeout,follow_redirects = True)
                    status_code = response.status_code

                    if response.history:
                        redirection = response.history[-1].headers["location"]
                        print(f"      {self.bold}{self.blue}{url}{self.reset} {self.bold}{self.white}[{self.reset}{status_code}{self.bold}{self.white}] -> {self.reset}{self.bold}{redirection}{self.reset}")
                    else:
                        print(f"      {self.bold}{self.blue}{url}{self.reset} {self.bold}{self.white}[{self.reset}{status_code}{self.bold}{self.white}]{self.reset}")

                    break
                    
                except httpx.TimeoutException:
                    failed_reason = "Timeout Error"

                except httpx.HTTPStatusError:
                    failed_reason = "Status code error"

                except httpx.RequestError:
                    failed_reason = "Request Error"

                except Exception:
                    failed_reason = "Unexpected Error"

                if attempt < max_retry:
                    await asyncio.sleep(retry_delay)

                else:
                    print(f"      {self.bold}{self.red}{url}{self.reset} {self.bold}{self.white}[{self.reset}{failed_reason}{self.bold}{self.white}]{self.reset}")


    async def prober(self,urls:list) -> None:
        """
            Async coroutine to probe the given urls.

            Args:
                urls (list)   : Urls to make to check status code.

            Returns:
                None
        """
        tasks = []
        timeout = httpx.Timeout(timeout = self.timeout)

        async with httpx.AsyncClient(timeout = timeout) as client_session:
            
            for url in urls:
                tasks.append(self.make_request(url.strip(),timeout,client_session))

            await asyncio.gather(*tasks)



    def run(self,urls:list) -> None:
        """
            Function to start the HttpProber.
            
            Args:
                urls    (list): Urls to make to check status code.

            Returns:
                list    :   Retruns the list of urls with its statuscodes in a dictionary.

        """
        # Calculation the completion time of http probing.
        start_time = perf_counter()
        asyncio.run(self.prober(urls))
        end_time = perf_counter()

        if self.verbose:
            print(f"[ + ] Http probing completed in: {end_time - start_time} sec")