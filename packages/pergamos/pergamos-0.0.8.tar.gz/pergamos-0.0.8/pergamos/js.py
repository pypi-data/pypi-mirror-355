toggleContent = f"""<script>
        // Toggle the visibility of the collapsible content
        function toggleContent(header) {{
            const content = header.nextElementSibling;
            const triangle = header.querySelector(".triangle");
            content.style.display = content.style.display === "none" || content.style.display === ""
                                    ? "block"
                                    : "none";
            // Toggle triangle direction
            if (content.style.display === "block") {{
                triangle.classList.add('expanded');
            }} else {{
                triangle.classList.remove('expanded');
            }}
        }}
        </script>
    """


switchTab = """<script>
    // Switch between tabs
    function switchTab(tabId) {
        let contents = document.getElementsByClassName('tab-content');
        for (let content of contents) {
            content.style.display = 'none';
        }
        document.getElementById(tabId).style.display = 'block';

        let buttons = document.getElementsByClassName('tab-button');
        for (let button of buttons) {
            button.classList.remove('active');
        }
        document.querySelector(`[onclick="switchTab('${tabId}')"]`).classList.add('active');
    }
    </script>
    """

# MathJax for latex rendering
mathjax = """
    <script>
        MathJax = {
            tex: { inlineMath: [['$', '$']] },
            svg: { fontCache: 'global' },
            options: { processHtmlClass: 'math-content' },
            macros: {
                beginenumerate: "\\begin{array}{l}",
                endenumerate: "\\end{array}",
                item: "\\quad \\bullet \\quad"
            }
        };
    </script>
    <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    """


saveobject = """
    <script>
function downloadHTML2() {
    const htmlContent = document.documentElement.outerHTML;
    const blob = new Blob([htmlContent], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement("a");
    a.href = url;
    a.download = "pergamos_output.html";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    
    URL.revokeObjectURL(url);
}
</script>
"""

save = """<script>
function downloadHTML(button) {
    const container = button.closest(".saveable") || button.closest(".container") || button.closest(".collapsible-container");
    if (!container) return;
    // Collect all style and script tags
    const styleTags = Array.from(document.querySelectorAll('style')).map(s => s.outerHTML).join(" ");
    const scriptTags = Array.from(document.querySelectorAll('script')).map(s => s.outerHTML).join(" ");
    const scripts = Array.from(document.querySelectorAll('script')).map(s => s.outerHTML).join(" ");
    
    console.log("CONTAINER HTML:", container?.outerHTML);
    console.log("SCRIPTS:", scripts);

    const fullHTML = `<!DOCTYPE html><html><head><meta charset="UTF-8">${styleTags}</head><body>${container.outerHTML}${scriptTags}</body></html>`;

    const blob = new Blob([fullHTML], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "pergamos_container.html";
    a.click();
    URL.revokeObjectURL(url);
}
</script>
"""


SCRIPTS = {'toggleContent': toggleContent, 'switchTab': switchTab, 'mathjax': mathjax, 
           'saveobject': saveobject, 'save': save}

