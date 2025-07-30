index = """<html>
    <head>
        <title>{{ page_title }}</title>
        <link rel='stylesheet' href='/static/style.css' />
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.4/jquery.min.js"></script>
        <script src="/static/script.js"></script>
    </head>
    <body>
        <div id="content">
            <div id="FIX">
                <div class="user">
                    <span id="name"></span>> <input type="text" id="FIX_input" autocomplete="off">
                </div>
            </div>
        </div>
        <script>
            let consolName = "{{ page_title }}".replace(" ", "_");
            document.getElementById("name").innerHTML = consolName;
            let shouldShowFix = true;
            let currentHistoryIndex = 0;
            let maxHistorySize = 0;
        </script>
    </body>
</html>
"""