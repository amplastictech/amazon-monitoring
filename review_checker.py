name: Amazon Review Checker
on:
  schedule:
    - cron: '0 * * * *'  # Runs hourly
  workflow_dispatch:

jobs:
  check-reviews:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Cache Python dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Cache Firefox and Geckodriver
        uses: actions/cache@v4
        with:
          path: |
            /opt/firefox
            /usr/local/bin/geckodriver
          key: ${{ runner.os }}-firefox-geckodriver-${{ hashFiles('**/review_checker.yml') }}
          restore-keys: |
            ${{ runner.os }}-firefox-geckodriver-

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y xvfb libgtk-3-0 libxtst6 libx11-xcb1 libdbus-glib-1-2

      - name: Install Python dependencies
        run: |
          python -m pip install --upgrade pip
          pip uninstall selenium -y || true
          pip install selenium==4.18.1 --no-cache-dir --force-reinstall
          pip install beautifulsoup4

      - name: Install Firefox
        run: |
          if [ ! -d "/opt/firefox" ]; then
            wget -O firefox.tar.bz2 "https://download.mozilla.org/?product=firefox-latest&os=linux64&lang=en-US"
            sudo mkdir -p /opt/firefox
            sudo tar -xjf firefox.tar.bz2 -C /opt/firefox --strip-components=1
            rm firefox.tar.bz2
          fi
          sudo ln -sf /opt/firefox/firefox /usr/bin/firefox

      - name: Install Geckodriver
        run: |
          if [ ! -f "/usr/local/bin/geckodriver" ]; then
            GECKODRIVER_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | jq -r '.tag_name')
            wget -O geckodriver.tar.gz "https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz"
            sudo tar -xzf geckodriver.tar.gz -C /usr/local/bin/
            sudo chmod +x /usr/local/bin/geckodriver
            rm geckodriver.tar.gz
          fi

      - name: Verify Selenium Installation
        run: |
          python -c "import selenium; print(f'Selenium version: {selenium.__version__}')"
          python -c "import selenium.common.exceptions; print('Exceptions module exists')" || echo "Exceptions import failed"

      - name: Run Python script
        env:
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
          DISPLAY: :99
        run: |
          Xvfb :99 -screen 0 1024x768x24 &
          sleep 3
          python review_checker.py
