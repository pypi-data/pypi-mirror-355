try:
    import asyncio
    import aiohttp
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
    def __init__(self,semaphore_count:int, timeout:int = 4,verbose:bool = False) -> None:
        self.timeout = timeout
        self.verbose = verbose
        self.semaphore = asyncio.Semaphore(semaphore_count)

    async def make_request(self,url:str,client_session:object) -> dict:
        """
            Async coroutine to make a request to the given url.

            Args:
                url (str)   : Url to make to check status code.
                client_session  (object):   The client session object which is used to make request to the url.

            Returns:
                dict    :   Retruns the dictionary of url with its statuscode.

                Example: 
                result = {
                        "url":"https://www.google.com",
                        "status":200
                    }
        """
        
        result = {
            "url":None,
            "status":None
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HttpProber/1.0.0;)",
            "Accept":"*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive"
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with self.semaphore:
            try:
                # Checking the url.
                if url.startswith("http://") or url.startswith("https://"):
                    pass
                else:
                    url = "https://" + url
                    
                # Making get request to the url.
                async with client_session.get(url ,headers = headers ,timeout = timeout) as response:
                    status_code = response.status
                    result["url"] = url
                    result["status"] = status_code

            except aiohttp.client_exceptions.InvalidURL:
                result["url"] = url
                result["status"] = "Invalid url"
            
            except asyncio.TimeoutError:
                result["url"] = url
                result["status"] = "Timeout Error"

            except aiohttp.ClientConnectorDNSError:
                result["url"] = url
                result["status"] = "Resolution Error"

            except aiohttp.client_exceptions.ClientResponseError:
                result["url"] = url
                result["status"] = "Response Error"
            
            except Exception:
                result["url"] = url
                result["status"] = "Unexpected Error"

            return result

    async def prober(self,urls:list) -> list:
        """
            Async coroutine to probe the given urls.

            Args:
                urls (list)   : Urls to make to check status code.

            Returns:
                list    :   Retruns the list of urls with its statuscodes in a dictionary.

                Example: 
                result = [
                {
                    "url":"https://www.google.com",
                    "status":200
                },{
                    "url":"https://www.facebook.com",
                    "status":200
                }
        """
        tasks = []
        timeout = aiohttp.ClientTimeout(self.timeout)

        async with aiohttp.ClientSession(timeout = timeout) as client_session:
            
            for url in urls:
                tasks.append(self.make_request(url.strip(),client_session))

            results = await asyncio.gather(*tasks)
                        
        return results


    def run(self,urls:list) -> list:
        """
            Function to start the HttpProber.
            
            Args:
                urls    (list): Urls to make to check status code.

            Returns:
                list    :   Retruns the list of urls with its statuscodes in a dictionary.

        """
        # Calculation the completion time of http probing.
        start_time = perf_counter()
        results = asyncio.run(self.prober(urls))
        end_time = perf_counter()

        if self.verbose:
            print(f"[ + ] Http probing completed in: {end_time - start_time} sec")

        return results
    
if __name__ == "__main__":

    urls = [
        "https://www.reddit.com",
        "https://www.bing.com",
        "https://www.yahoo.com",
        "https://www.netflix.com",
        "https://www.nytimes.com",
        "https://www.theguardian.com",
        "https://www.cloudflare.com",
        "https://www.ibm.com",
        "https://www.intel.com",
        "https://www.adobe.com",
        "https://www.canva.com",
        "https://www.salesforce.com",
        "https://www.dropbox.com",
        "https://www.spotify.com",
        "https://www.airbnb.com",
        "https://www.booking.com",
        "https://www.twitch.tv",
        "https://www.nike.com",
        "https://www.samsung.com",
        "https://www.paypal.com",
        "https://www.office.com",
        "https://www.stackexchange.com",
        "https://www.cloudflarestatus.com",
        "https://www.iana.org",
        "https://www.mozilla.org",
        "https://www.python.org",
        "https://www.nodejs.org",
        "https://www.docker.com",
        "www.kali.org",
        "www.w3.org"
    ]

    probber = HttpProber(verbose = True)
    results = probber.run(urls)

    print(results)