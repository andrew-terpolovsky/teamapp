#DoIQApp#

1. Install Python Dependencies
```
    pip install -r requirements.txt
```

2. Install node utils and bower dependencies
```
    npm install && bower install
```

3. Build and watch Static Files
```
    gulp && gulp watch
```

4. Setup local settings
```
    export DJANGO_SETTINGS_MODULE=config.settings.local
```

5. Run socket server
```
    ./manage.py socketserver
```
