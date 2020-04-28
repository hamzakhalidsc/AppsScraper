import os
import shutil
import sqlite3
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options


# -----------------------------------------------
# download function for apks of apk pure and xiomi
def download_apk(download_link, app_dir):
    print('-----------------------------')
    print('Opening Download Link...')

    driver.get(download_link)

    print('Waiting for files to appear...')

    # wait 180 seconds for the app to download and show up
    try:
        c = 0
        found = False
        while not found:

            for dirpath, dirnames, files in os.walk(download_dir):
                if len(files) != 0:
                    found = True
                    break

            time.sleep(1)
            c += 1

            if c == 180:
                print('Error: Files not Appeared.')
                raise Exception('Failed')

        print('Files Appeared!')

        print('Waiting for files to download...')

        c = 0
        time.sleep(2)

        while True:
            if (len(os.listdir(download_dir))) == 1:
                break

            if c == 500:
                print('Error: Download Issue')
                os.system('del "' + download_dir + '*" /Q')
                raise Exception('Failed')

            time.sleep(1)
            c += 1

        time.sleep(2)

        print('File Downloaded!')

        # rename the file and move it to its folder
        for file in os.listdir(download_dir):
            if file.endswith(".apk"):
                print('Moving File...')
                shutil.move(download_dir + file, app_dir + package + ".apk")

        print('File Moved')
        print('-----------------------------')
        return True

    except:
        print("Failed")

        print('-----------------------------')
        return False


# -----------------------------------------------


# the db which maintains record of apps downloaded
conn = sqlite3.connect('g_p_apps.sqlite', timeout=10)
cur = conn.cursor()

options = Options()

#  Code to disable notifications pop up of Chrome Browser
options.add_argument("--disable-notifications")
#options.add_argument("--headless")

download_dir = os.getcwd() + "\\tmp\\"

# empty left over downloads
os.system('del "' + download_dir + '*" /Q')

profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.dir", download_dir)
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.android.package-archive")

# initialization
driver = webdriver.Firefox(executable_path=os.getcwd() + '\\geckodriver.exe', firefox_profile=profile,
                           firefox_options=options)
driver.maximize_window()

cur.execute("SELECT package from APPS where error is null")
results = cur.fetchall()

count = 0

for a in results:

    # commit to db after every 10 apps are checked
    if count == 10:
        conn.commit()
        count = 0

    count += 1

    package = a[0]
    print("-------------------------------------------------------------------")
    print("Package:", package)

    error = 0

    p_ok = False
    g_ok = False

    try:
        "APK Pure"
        p_url = "https://apkpure.com/hello/" + package
        driver.get(p_url)

        if driver.title == '404' or driver.title == '410 Error - Page Deleted or Gone':
            error = 'p_notfound'
            print(error)
            cur.execute('Update Apps set error = ? where package = ?', (error, package,))

            continue

        p_link = "https://apkpure.com/hello/" + package + "/download?from=details"
        p_ok = True

        "Google"
        g_url = "https://play.google.com/store/apps/details?id=" + package

        driver.get(g_url)

        if driver.title == 'Not Found':
            error = 'g_notfound'
            print(error)
            cur.execute('Update Apps set error = ? where package = ?', (error, package,))

            continue

        g_ok = True

        "IF APP EXISTS ON BOTH APPSTORES, ONLY THEN DOWNLOAD IT FROM THE APPSTORES"
        if g_ok and p_ok:


            print("Downloading from pure..")
            downloaded = download_apk(p_link, os.getcwd() + "\\pure_apps\\")

            if downloaded:
                cur.execute('Update Apps set p_retrieved = 1 where package = ?',
                            (package,))
            else:
                cur.execute('Update Apps set p_retrieved = -1 where package = ?', (package,))
            
            # --------------------------------------------------------
            print("Downloading from google..")
            try:
                os.system('gplaycli -d ' + package + ' -f "' + '.\google_apps"' + ' -p')

                # check if a file of that apk is created
                dir = os.getcwd() + "\\google_apps\\" + package + ".apk"

                time.sleep(2)

                save = False

                # check if that directory is empty
                if os.path.exists(dir):
                    save = True

                if save:
                    cur.execute('Update Apps set g_retrieved = 1 where package = ?', (package,))

                    print(package, ": Google Download Successful")
                else:
                    cur.execute('Update Apps Set g_retrieved= -1 where package = ?', (package,))
                    print(package, ": Failed")

            except Exception as e:
                cur.execute('Update Apps Set g_retrieved= -1 where package = ?', (package,))
                print(package, ": Failed")

            cur.execute('Update apps set error = 0 where package = ? ', (package,))
            print("Done!")
            print("----------------------------------------------------------------------")

    except:
        print("Error!")

conn.commit()

driver.close()

print('\n\nProcess Successfully finished!!!!!\n\n')
