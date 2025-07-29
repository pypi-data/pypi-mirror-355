try:
    import pytest
    import aiohttp
    from http_prober.modules.prober.prober import HttpProber

except ImportError as Ie:
    print(f"[ + ] Import Error [modules.tests.prober]: {Ie}")
    exit(1)

# Initializing HttpProber class to test.
prober = HttpProber(semaphore_count = 100)

@pytest.mark.asyncio
async def test_make_request() -> bool:
    """
        Async coroutine to test the make_request coroutine in HttpProber class with expected result. 

        Args:
            None
            
        Returns:
            bool    :   Returns True if expected result match with test result.
                
    """
    url = 'https://www.google.com'
    status = 200

    async with aiohttp.ClientSession() as client_session:
        result = await prober.make_request(url,client_session)

    assert result["status"] == status

@pytest.mark.asyncio
async def test_prober() -> bool:
    """
        Async coroutine to test the prober coroutine in HttpProber class with expected result. 

        Args:
            None
            
        Returns:
            bool    :   Returns True if expected result match with test result.
                
    """
    urls = [
        "https://www.google.com",
        "https://www.instagram.com",
        "https://www.facebook.com"
    ]
    expected = [
                {
                    "url":"https://www.google.com",
                    "status":200
                },
                {
                    "url":"https://www.instagram.com",
                    "status":200
                },
                {
                    "url":"https://www.facebook.com",
                    "status":200
                }
            ]
    results = await prober.prober(urls)

    assert expected == results

def test_run() -> bool:
    """
        Function to test the run function in HttpProber class with expected result. 

        Args:
            None
            
        Returns:
            bool    :   Returns True if expected result match with test result.
                
    """
    urls = [
        "https://www.google.com",
        "https://www.instagram.com",
        "https://www.facebook.com"
    ]
    expected = [
                {
                    "url":"https://www.google.com",
                    "status":200
                },
                {
                    "url":"https://www.instagram.com",
                    "status":200
                },
                {
                    "url":"https://www.facebook.com",
                    "status":200
                }
            ]
    
    results = prober.run(urls)

    assert expected == results
