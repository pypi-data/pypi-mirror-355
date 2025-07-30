# minwei_tools

### This tools contain 3 major function

1. Dotter : Display animated text on screen during long missions
2. re_result : A Rust-like approach to error handling
3. server : A file transfer server 
4. us_doc : A `uv` doc generator

# Install

```bash
pip install minwei_tools
```

# Usage

* ## File Transfer server

    ```python
    python -m minwei_tools.server -p {port} -h {host}
    ```

* ## Dotter

    ![alt text](loading.gif)

    ```python
    from minwei_tools import Dotter, piano, slash
    from time import sleep

    with Dotter(message="[*] Testing 1", cycle=slash, delay=0.1, show_timer=1) as d:
        sleep(10)
        d.update_message("[-] Testing 2", delay=0.1)
        sleep(2)
    ```

    Also support an `async` dotter

    ```python
    from time import sleep
    import asyncio

    from minwei_tools import AsyncDotter

    async def main():
        async with AsyncDotter("Thinking", show_timer=True, delay=0.1):
            await asyncio.sleep(120)

    asyncio.run(main())
    ```

* ## rs_result

    ```python
    from minwei_tools.rs_result import Result, Ok, Err

    def devide(a: int, b: int) -> Result[int, str]:
        if b == 0:
            return Err("Division by zero error")
        return Ok(a // b)

    """
    >>> result : Result[int, str] = devide(10, 0)
    >>> result.is_ok()
    False
    >>> result.is_err()
    >>> result : Result[int, str] = devide(10, 2)
    >>> result.is_ok()
    True
    >>> result.unwrap()
    5
    """

    result : Result[int, str] = devide(10, 0)
    match result:
        case Ok(value):
            print(f"Result: {value}")
        case Err(value):
            print(f"Error: {value}")
            
    result : Result[int, str] = devide(10, 2)
    match result:
        case Ok(value):
            print(f"Result: {value}")
        case Err(value):
            print(f"Error: {value}")
    ```

* ## uv doc
    ```bash
    python -m minwei_tools.uv_doc -p {PROJECT_NAME}
    ```

    ```
    -h, --help            show this help message and exit
    -p PROJECT_NAME, --project_name PROJECT_NAME
                            Name of the project. Defaults to the current directory name.
    -o OUTPUT, --output OUTPUT
                            Output file name. Defaults to README.md.
    -d DIRECTORY, --directory DIRECTORY
                            Directory to scan. Defaults to the current working directory.
    ```