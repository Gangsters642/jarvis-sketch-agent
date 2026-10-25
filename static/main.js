document.addEventListener("DOMContentLoaded", () => {
    const codeInput = document.getElementById("code-input");
    const formatSelect = document.getElementById("format-select");
    const projectNameInput = document.getElementById("project-name");
    const generateBtn = document.getElementById("generate-btn");
    const clearBtn = document.getElementById("clear-btn");
    const statusBox = document.getElementById("status-box");
    const canvasContainer = document.getElementById("canvas-container");
    const downloadBtn = document.getElementById("download-btn");
    const androidAppBtn = document.getElementById("android-app-btn");
    const refreshProjectsBtn = document.getElementById("refresh-projects-btn");
    const projectListUl = document.getElementById("project-list-ul");

    const SAMPLES = {
        svg: '<circle cx="250" cy="250" r="120" stroke="#00f0ff" fill="rgba(0,240,255,0.15)" stroke-width="4" />\n<line x1="250" y1="50" x2="250" y2="450" stroke="#00f0ff" stroke-width="1.5" stroke-dasharray="5,5" />\n<line x1="50" y1="250" x2="450" y2="250" stroke="#00f0ff" stroke-width="1.5" stroke-dasharray="5,5" />',
        json: '{\n  "width": 500,\n  "height": 500,\n  "background": "#040811",\n  "shapes": [\n    { "type": "rect", "x": 100, "y": 100, "width": 300, "height": 300, "stroke": "#00f0ff", "fill": "none", "stroke-width": "3" },\n    { "type": "circle", "cx": 250, "cy": 250, "r": 80, "stroke": "#00e676", "fill": "rgba(0,230,118,0.1)", "stroke-width": "2" },\n    { "type": "text", "x": 150, "y": 255, "fill": "#00f0ff", "font-size": "24", "text_content": "JARVIS AGENT" }\n  ]\n}',
        coords: 'CANVAS 500 500\nCIRCLE 250 250 120 #00f0ff rgba(0,240,255,0.1) 3\nRECT 125 125 250 250 #00e676 none 2\nLINE 50 250 450 250 #ff3b5c 1.5'
    };

    let currentFilename = null;

    formatSelect.addEventListener("change", () => {
        const fmt = formatSelect.value;
        if (SAMPLES[fmt] && (!codeInput.value.trim() || confirm("Sample code load karen? Current code replace ho jaye ga."))) {
            codeInput.value = SAMPLES[fmt];
        }
    });

    if (!codeInput.value.trim()) {
        codeInput.value = SAMPLES.svg;
    }

    function showStatus(msg, isError = false) {
        statusBox.textContent = msg;
        statusBox.className = "status-box " + (isError ? "err" : "ok");
    }

    generateBtn.addEventListener("click", async () => {
        const code = codeInput.value;
        const fmt = formatSelect.value;
        const name = projectNameInput.value.trim() || "jarvis_sketch";

        generateBtn.disabled = true;
        generateBtn.textContent = "Processing...";
        showStatus("JARVIS generating sketch...");

        try {
            const res = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, format: fmt, name, save: true })
            });
            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.message || "Generation error.");
            }

            canvasContainer.innerHTML = data.svg;
            showStatus(data.message);

            if (data.file_info && data.file_info.filename) {
                currentFilename = data.file_info.filename;
                downloadBtn.disabled = false;
                androidAppBtn.disabled = false;
            }
            loadProjects();
        } catch (err) {
            showStatus(err.message, true);
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = "Generate Sketch";
        }
    });

    clearBtn.addEventListener("click", () => {
        codeInput.value = "";
        canvasContainer.innerHTML = '<span class="placeholder-text">Preview area khali hai. Code enter kar ke Generate dabayen.</span>';
        statusBox.className = "status-box";
        currentFilename = null;
        downloadBtn.disabled = true;
        androidAppBtn.disabled = true;
    });

    downloadBtn.addEventListener("click", () => {
        if (!currentFilename) return;
        window.location.href = `/api/download/${currentFilename}`;
    });

    androidAppBtn.addEventListener("click", async () => {
        if (!currentFilename) return;
        showStatus("Opening Android app chooser...");
        try {
            const res = await fetch("/api/open-android", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: currentFilename })
            });
            const data = await res.json();
            showStatus(data.message, !data.success);
        } catch (err) {
            showStatus("Android app open karne mein error aaya.", true);
        }
    });

    async function loadProjects() {
        try {
            const res = await fetch("/api/projects");
            const data = await res.json();
            if (data.success && data.projects) {
                renderProjects(data.projects);
            }
        } catch (err) {
            console.error("Failed to load projects history", err);
        }
    }

    function renderProjects(projects) {
        if (!projects || projects.length === 0) {
            projectListUl.innerHTML = '<li class="project-item placeholder-text">Koi saved sketch nahi mila.</li>';
            return;
        }
        projectListUl.innerHTML = "";
        projects.forEach(p => {
            const li = document.createElement("li");
            li.className = "project-item";
            li.innerHTML = `<span><b>${p.filename}</b> (${p.size_kb} KB)<br><small style="color:var(--text-muted);">${p.modified}</small></span>
                            <button data-filename="${p.filename}" class="load-proj-btn">Load</button>`;
            projectListUl.appendChild(li);
        });

        document.querySelectorAll(".load-proj-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const fname = btn.getAttribute("data-filename");
                try {
                    const r = await fetch(`/api/projects/${fname}`);
                    const d = await r.json();
                    if (d.success) {
                        codeInput.value = d.svg;
                        formatSelect.value = "svg";
                        canvasContainer.innerHTML = d.svg;
                        currentFilename = d.filename;
                        projectNameInput.value = d.filename.replace(/_\d{8}_\d{6}\.svg$/, "");
                        downloadBtn.disabled = false;
                        androidAppBtn.disabled = false;
                        showStatus(`Loaded project: ${d.filename}`);
                    }
                } catch (e) {
                    showStatus("Project load karne mein error aaya.", true);
                }
            });
        });
    }

    refreshProjectsBtn.addEventListener("click", loadProjects);

    loadProjects();
});
