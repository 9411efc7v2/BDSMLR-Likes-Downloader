r"""
Extract image URL for your liked posts and output to .txt file. Does not work for videos. 

Gallery-dl integration for seamless downloading of output file.

Set login credentials using [-u] and [-p] flags, or change "default=none" to your username/password in the argument parser section at the end.
    
[Optional] Provide a cookies.txt file with [-c] to load session cookies and skip login eg. -c "C:\User\MyFolder\cookies.txt" 

If output file is in same directory with same name as set with [-o] (default = "bdsmlr_likes.txt"), scraped URLs will be checked against list and duplicates will be skipped.
"""


import argparse
import random
import time ##Spinner timing
import threading ##Spinner loading animation 
import requests
from lxml import html
from colorama import Fore, Style, init ##Coloured text

## Other spinners, change 'chars' in spinner():
##     BASIC = [-/|\\]
##     ARROW = [←↖↑↗→↘↓↙]
##     VERT_BAR = [▁▃▄▅▆▇█▇▆▅▄▃]
##     HORIZ_BAR = [▉▊▋▌▍▎▏▎▍▌▋▊▉]
##     SPIN_RECT = [▖▘▝▗]
##     ELAST_BAR = [▌▀▐▄]
##     TETRIS = [┤┘┴└├┌┬┐]
##     TRIANGLE = [◢◣◤◥]
##     SQUARE_QRT = [◰◳◲◱]
##     CIRCLE_QRT = [◴◷◶◵]
##     CIRCLE_HLF = [◐◓◑◒]
##     BALLOON = [.oO@*]
##     BLINK = [◡◡⊙⊙◠◠]
##     TURN = [◜  ◝ ◞◟ ]
##     LOSANGE = [◇◈◆]
##     BRAILLE = [⣾⣽⣻⢿⡿⣟⣯⣷]

def spinner(label, stop_event):
    chars = "◢◣◤◥"
    i = 0
    while not stop_event.is_set():
        print(f"\r{Fore.CYAN}{chars[i % len(chars)]} {label}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print("\r" + " " * (len(label) + 4) + "\r", end="", flush=True)

def main(args):
    init(autoreset=True)

    ## Setup
    username = args.username
    password = args.password
    start_page = max(args.start_page, 1)
    end_page = args.end_page
    if end_page:
        if end_page <= 0:
            raise SystemExit("End page must be 1 or greater!")
    output_fname = args.output
    tag = args.tag ## Custom label for log messages, set with --tag
    
    ## Load existing URLs from output file to avoid duplicates
    existing_urls = set()
    try:
        with open(output_fname, "r") as f:
            existing_urls = {line.strip() for line in f if line.strip()}
        print(f"{Style.DIM}{Fore.YELLOW}Loaded {len(existing_urls)} existing URLs from {output_fname}")
    except FileNotFoundError:
        pass

    ## Session setup
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://bdsmlr.com/likes",
        "Accept-Language": "en-US,en;q=0.9",
    })

    ## Authentication // loads session cookie if provided with -c , otherwise logs in with credentials
    if args.cookies_file:
        import http.cookiejar
        jar = http.cookiejar.MozillaCookieJar(args.cookies_file)
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies.update(jar)
        print(f"{Style.DIM}{Fore.GREEN}Loaded cookies from {args.cookies_file}")
    else:
        login_page = html.fromstring(session.get("https://bdsmlr.com/login").text)
        login_hidden_value = login_page.xpath(
            '//*[@class="form_loginform"]/input[@type="hidden"]/@value'
        )[0]
        form_values = {
            "email": username,
            "password": password,
            "_token": login_hidden_value,
        }
        rv = session.post("https://bdsmlr.com/login", data=form_values)
        if rv.ok:
            print(f"{Fore.GREEN}[{tag}] Logged in ...")
        else:
            print(f"{Fore.RED}[{tag}] Login failed with status {rv.status_code}!")

    ## Fetch page status, colour code status codes
    def fetch_page(pg, retry=False):
        r = session.get("https://bdsmlr.com/likes", params={"page": pg}, timeout=300)
        if r.status_code < 300:
            status_color = Fore.GREEN if retry else Fore.WHITE ## green: successful retry
        elif r.status_code < 400:
            status_color = Fore.YELLOW ## redirect
        else:
            status_color = Fore.RED ## error

        dim = Style.DIM if status_color == Fore.WHITE else ""
        print(f"{dim}| {status_color}Status: {r.status_code} | Page {pg} | URL: {r.url}{Style.RESET_ALL}")

        if r.status_code >= 400:
            raise Exception(f"Bad status code: {r.status_code}")
        
        ## Re-Authentication // Session expired mid-run — retry login/page
        p = html.fromstring(r.text)
        if p.xpath('//form[@class="form_loginform"]'):
            print(f"{Style.DIM}[{tag}]{Style.RESET_ALL}{Fore.YELLOW} Session expired, re-logging in...")
            session.cookies.clear()
            time.sleep(5)
            new_login_page = html.fromstring(session.get("https://bdsmlr.com/login").text)
            token = new_login_page.xpath('//*[@class="form_loginform"]/input[@type="hidden"]/@value')[0]
            rv2 = session.post("https://bdsmlr.com/login", data={
                "email": username,
                "password": password,
                "_token": token,
            })
            print(f"{Fore.YELLOW}Re-login status: {rv2.status_code} | URL: {rv2.url}")
            print(f"{Fore.YELLOW}Cookies after re-login: {dict(session.cookies)}")
            time.sleep(3)
            r = session.get("https://bdsmlr.com/likes", params={"page": pg}, timeout=300)
            p = html.fromstring(r.text)
        return p

    ## Fetch likes
    print(f"{Style.DIM}[{tag}]{Style.RESET_ALL}{Fore.GREEN} Getting Likes ...")

    done = False
    end_page_text = end_page or "?"
    image_count = 0
    pages_success = 0
    pages_skipped = 0
    skipped_pages = []
    current_page = start_page
    relogin_attempts = 0
    prev_image_count = 0

    while not done:
        if end_page_text == "?":
            page_total = f"{Style.DIM}{end_page_text}{Style.RESET_ALL}"
        elif current_page == end_page:
            page_total = f"{Fore.CYAN}{end_page_text}{Fore.RESET}"
        else:
            page_total = str(end_page_text)

        ## page_total = f"{Fore.CYAN}{end_page_text}{Fore.RESET}" if current_page == end_page else str(end_page_text)
        ## print(
        ##     f"{Style.DIM}[{tag}]{Style.RESET_ALL} Scraping page {Fore.CYAN}{current_page}{Fore.RESET}/{page_total} ...",
        ##     flush=True,
        ##)

        ## Spinner & 'Retrying...' countdown timer
        page = None
        had_failure = False
        for attempt in range(1, 4):
            stop = threading.Event()
            t = threading.Thread(target=spinner, args=(f"{Fore.WHITE}Scraping page {Fore.CYAN}{current_page}{Fore.RESET}/{page_total} ... ", stop))
            t.start()
            try:
                page = fetch_page(current_page, retry=had_failure)
                if page is None:
                    raise Exception(f"{Fore.RED}No page returned")
                break
            except Exception as e:
                had_failure = True
                stop.set()
                t.join()
                print(f"{Fore.YELLOW}Error fetching page (attempt {attempt}/3): {e}")
                if attempt < 3:
                    for i in range(10, 0, -1):
                        print(f"\r{Fore.YELLOW}Retrying in {i}s...  ", end="", flush=True)
                        time.sleep(1)
                    print()
            finally:
                stop.set()
                t.join()
        else:
            print(f"{Fore.RED}Failed after 3 attempts, stopping.")
            pages_skipped += 1
            skipped_pages.append(current_page)
            break

        links = page.xpath('//*[@class="magnify"]/@href')

        if not links and page.xpath('//form[@class="form_loginform"]'):
            relogin_attempts += 1
            if relogin_attempts >= 3:
                print(f"{Style.DIM}[{tag}]{Style.RESET_ALL}{Fore.RED}Stuck on login page after 3 attempts, stopping.")
                pages_skipped += 1
                skipped_pages.append(current_page)
                break
            print(f"{Style.DIM}[{tag}]{Style.RESET_ALL}{Fore.YELLOW} Got login page on {current_page}, retrying (attempt {relogin_attempts}/3)...")
            time.sleep(10)
            continue

        relogin_attempts = 0
        pages_success += 1

        if len(links) == 0:
            pages_skipped += 1
            pages_success -= 1
            skipped_pages.append(current_page)
            current_page += 1
            continue

        print(f"{Style.DIM}Found {len(links)} {Fore.WHITE}images.")
        
        ## Check against existing output file, skip duplicates
        new_links = [l for l in links if l not in existing_urls]
        existing_urls.update(new_links)
        image_count += len(new_links)

        dupes = len(links) - len(new_links)
        if dupes > 0:
            print(f"{Style.DIM}{Fore.YELLOW}{dupes} URLs already in output file.")

        if new_links:
            links_text = "\n".join(new_links) + "\n"
            with open(output_fname, "a") as f:
                f.write(links_text)

        
        count_color = Fore.GREEN if image_count > prev_image_count else Fore.YELLOW
        zero_color = Fore.YELLOW if len(new_links) == 0 else Fore.GREEN
        print(f"Collected {zero_color}{len(new_links)}{Fore.RESET} images ({count_color}{image_count}{Fore.RESET} total)")
        prev_image_count = image_count

        time.sleep(random.uniform(2, 5))

        current_page += 1

        ## Is there more pages?
        if not page.xpath('//a[@rel="next"]/@href'):
            done = True

        ## Met end page
        if end_page and current_page > end_page:
            done = True

    ## Summary
    skipped_str = (
        f"{Fore.RED}({pages_skipped} skipped){Style.RESET_ALL}"
        if pages_skipped > 0
        else f"({Fore.GREEN}0 {Fore.CYAN}skipped)"
    )
    print(
        f"{Style.NORMAL}{Fore.CYAN}Done! Collected {Fore.GREEN}{Style.BRIGHT}{image_count} {Fore.CYAN}{Style.NORMAL}images over "
        f"{Fore.GREEN}{Style.BRIGHT}{pages_success + pages_skipped} {Style.NORMAL}{Fore.CYAN}pages {skipped_str}, "
        f"{Style.NORMAL}saved to {Fore.YELLOW}{Style.BRIGHT}{output_fname}{Style.NORMAL}{Fore.CYAN}."
    )

    ## Post-run prompts
    if skipped_pages:
        answer = input("Would you like a report of skipped pages? (y/n): ")
        if answer.strip().lower() == 'y':
            print("Skipped pages:")
            for pg in skipped_pages:
                print(f"{Fore.RED}  Page {pg}")
        
        retry = input("Would you like to retry skipped pages? (y/n): ")
        if retry.strip().lower() == 'y':
            print(f"{Fore.YELLOW}Retrying skipped pages: {skipped_pages}")
            for pg in skipped_pages:
                print(f"{Style.DIM}[{tag}]{Style.RESET_ALL} Retrying page {Fore.CYAN}{pg}{Fore.RESET} ...")
                try:
                    page = fetch_page(pg)
                    links = page.xpath('//*[@class="magnify"]/@href')
                    if links:
                        image_count += len(links)
                        links_text = "\n".join(links) + "\n"
                        with open(output_fname, "a") as f:
                            f.write(links_text)
                        print(f"Collected {Fore.GREEN}{len(links)}{Fore.RESET} images from page {pg}.")
                    else:
                        print(f"{Fore.RED}Still no images on page {pg}, giving up.")
                except Exception as e:
                    print(f"{Fore.RED}Failed to fetch page {pg}: {e}")

    answer2 = input(f"{Fore.YELLOW}Restart{Style.RESET_ALL}, {Fore.GREEN}Download {Style.RESET_ALL}or {Fore.RED}Terminate{Style.RESET_ALL}? (r/d/t): ")
    if answer2.strip().lower() == 't':
        print(f"{Fore.GREEN}--------------------------------- Export complete! Goodbye! ---------------------------------") 
    elif answer2.strip().lower() == 'd':
        import subprocess
        print(f"{Style.BRIGHT}{Fore.GREEN}Export complete! Starting gallery-dl download from {output_fname}...") 
        result = subprocess.run(["gallery-dl", "-i", output_fname])
        if result.returncode == 0:
            print(f"{Fore.GREEN}--------------------------------- Download complete! Goodbye! ---------------------------------")
        else:
            print(f"{Fore.RED}gallery-dl finished with errors (code {result.returncode}).")          
    elif answer2.strip().lower() == 'r':
        main(args)          

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-u", "--username", default=None)
    parser.add_argument("-p", "--password", default=None)
    parser.add_argument("-s", "--start-page", type=int, default=1, help="start page")
    parser.add_argument("-e", "--end-page", type=int, default=None, help="end page")
    parser.add_argument("-o", "--output", default="bdsmlr_likes.txt", help="output filename")
    parser.add_argument("-c", "--cookies-file", default=None, help="path to Netscape cookies.txt")
    parser.add_argument("--tag", default=None, help="custom tag for log messages")
    args = parser.parse_args()
    if args.tag is None:
        args.tag = args.username
    main(args)
