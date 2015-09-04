
pageWrapper = """<html><head>
%(htmlHead)s
</head>
<body>
%(htmlBody)s
</body>
</html>
"""

indexWrapper = """
<h1>%(title)s</h1>
%(introduction)s
<ul>
%(items)s
</ul>
"""

item = """   <li>%(item)s</li>"""

attribute = '''   <li><span title="%(keyTitle)s"><b>%(key)s</b></span>: %(value)s</li>'''

tabItem = "<td>%s</td>"
tabRow = "<tr>%s</tr>\n"
table = """<table%(attributes)s>%(head)s%(content)s</table>"""

fTabItem = '<td><input name="%s" value="%s" type="text"/></td>'
fTabRow = "<tr>%s</tr>\n"
fTable = """<form action="http://localhost:8051/" method="POST" name="myForm">
 <input type="submit" value="Submit">
 <input type="hidden" name="formid" value="%(formid)s">
<table%(attributes)s>%(head)s%(fContent)s</table></form>"""

