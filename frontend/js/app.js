/* =========================================
   CLOUDNOTES - FLASK API CLIENT
========================================= */


const API_URL =
    "http://127.0.0.1:5000";


/* =========================================
   PAGE INITIALIZATION
========================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const loginForm =
            document.getElementById(
                "loginForm"
            );


        const uploadForm =
            document.getElementById(
                "uploadForm"
            );


        const fileInput =
            document.getElementById(
                "noteFile"
            );


        if (loginForm) {

            loginForm.addEventListener(
                "submit",
                handleLogin
            );

        }


        if (uploadForm) {

            uploadForm.addEventListener(
                "submit",
                handleUpload
            );

        }


        if (fileInput) {

            fileInput.addEventListener(
                "change",
                showSelectedFile
            );

        }


        loadTheme();


        /*
         * Only call API functions on
         * pages where their elements exist.
         */

        if (
            document.getElementById(
                "totalFiles"
            )
        ) {

            updateDashboard();

        }


        if (
            document.getElementById(
                "filesTable"
            )
        ) {

            renderFiles();

        }

    }
);


/* =========================================
   LOGIN
========================================= */

async function handleLogin(event) {

    event.preventDefault();


    const email =
        document.getElementById(
            "email"
        ).value.trim();


    const password =
        document.getElementById(
            "password"
        ).value;


    const message =
        document.getElementById(
            "loginMessage"
        );


    try {

        const response =
            await fetch(
                `${API_URL}/api/login`,
                {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        email: email,

                        password: password

                    })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Login failed"
            );

        }


        sessionStorage.setItem(
            "cloudnotes_user",
            JSON.stringify(
                data.user
            )
        );


        message.className =
            "message success";


        message.textContent =
            "Login successful. Redirecting...";


        setTimeout(
            function () {

                window.location.href =
                    "dashboard.html";

            },
            600
        );


    }

    catch (error) {

        message.className =
            "message error";


        message.textContent =
            error.message;

    }

}


/* =========================================
   PASSWORD TOGGLE
========================================= */

function togglePassword() {

    const password =
        document.getElementById(
            "password"
        );


    const icon =
        document.getElementById(
            "passwordIcon"
        );


    if (!password) return;


    if (
        password.type ===
        "password"
    ) {

        password.type =
            "text";


        icon.className =
            "bi bi-eye-slash";

    }

    else {

        password.type =
            "password";


        icon.className =
            "bi bi-eye";

    }

}


/* =========================================
   LOGOUT
========================================= */

function logout() {

    sessionStorage.removeItem(
        "cloudnotes_user"
    );


    window.location.href =
        "index.html";

}


/* =========================================
   GET CURRENT USER
========================================= */

function getCurrentUser() {

    const user =
        sessionStorage.getItem(
            "cloudnotes_user"
        );


    if (!user) {

        return {
            name: "Imad Khan",
            email: "admin@cloudnotes.com"
        };

    }


    try {

        return JSON.parse(user);

    }

    catch {

        return {
            name: "Imad Khan",
            email: "admin@cloudnotes.com"
        };

    }

}


/* =========================================
   DASHBOARD
========================================= */

async function updateDashboard() {

    try {

        const response =
            await fetch(
                `${API_URL}/api/dashboard`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                "Unable to load dashboard"
            );

        }


        const stats =
            data.stats;


        const totalFiles =
            document.getElementById(
                "totalFiles"
            );


        const myUploads =
            document.getElementById(
                "myUploads"
            );


        const storageUsed =
            document.getElementById(
                "storageUsed"
            );


        const totalSubjects =
            document.getElementById(
                "totalSubjects"
            );


        if (totalFiles) {

            totalFiles.textContent =
                stats.totalFiles;

        }


        if (myUploads) {

            myUploads.textContent =
                stats.myUploads;

        }


        if (storageUsed) {

            storageUsed.textContent =
                Number(
                    stats.storageUsed
                ).toFixed(1)
                + " MB";

        }


        if (totalSubjects) {

            totalSubjects.textContent =
                stats.totalSubjects;

        }


        await renderRecentFiles();

    }

    catch (error) {

        console.error(
            "Dashboard error:",
            error
        );

    }

}


/* =========================================
   GET FILES FROM FLASK
========================================= */

async function getFiles() {

    const response =
        await fetch(
            `${API_URL}/api/files`
        );


    const data =
        await response.json();


    if (!response.ok) {

        throw new Error(
            data.message ||
            "Failed to load files"
        );

    }


    return data.files || [];

}


/* =========================================
   RECENT FILES
========================================= */

async function renderRecentFiles() {

    const container =
        document.getElementById(
            "recentFiles"
        );


    if (!container) return;


    try {

        const files =
            await getFiles();


        const recent =
            files.slice(0, 5);


        container.innerHTML = "";


        if (recent.length === 0) {

            container.innerHTML = `

                <tr>

                    <td colspan="5"
                        style="text-align:center">

                        No notes uploaded yet.

                    </td>

                </tr>

            `;

            return;

        }


        recent.forEach(
            function (file) {

                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `

                    <td>

                        <div class="file-name">

                            <div class="file-icon">

                                <i class="bi bi-file-earmark-pdf"></i>

                            </div>

                            ${escapeHTML(file.title)}

                        </div>

                    </td>


                    <td>

                        <span class="badge">

                            ${escapeHTML(file.subject)}

                        </span>

                    </td>


                    <td>

                        ${escapeHTML(
                    file.uploadedBy
                )}

                    </td>


                    <td>

                        ${formatDate(
                    file.date
                )}

                    </td>


                    <td>

                        <button
                            class="action-btn download-btn"
                            onclick="downloadFile(${file.id})"
                            title="Download">

                            <i class="bi bi-download"></i>

                        </button>

                    </td>

                `;


                container.appendChild(
                    row
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Recent files error:",
            error
        );

    }

}


/* =========================================
   ALL FILES
========================================= */

async function renderFiles() {

    const table =
        document.getElementById(
            "filesTable"
        );


    if (!table) return;


    const emptyState =
        document.getElementById(
            "emptyState"
        );


    const searchInput =
        document.getElementById(
            "searchFiles"
        );


    const subjectFilter =
        document.getElementById(
            "subjectFilter"
        );


    try {

        const files =
            await getFiles();


        const search =
            searchInput
                ? searchInput.value
                    .toLowerCase()
                    .trim()
                : "";


        const subject =
            subjectFilter
                ? subjectFilter.value
                : "all";


        const filtered =
            files.filter(
                function (file) {

                    const matchesSearch =

                        file.title
                            .toLowerCase()
                            .includes(search)

                        ||

                        file.filename
                            .toLowerCase()
                            .includes(search)

                        ||

                        file.subject
                            .toLowerCase()
                            .includes(search);


                    const matchesSubject =

                        subject === "all"

                        ||

                        file.subject ===
                        subject;


                    return (
                        matchesSearch &&
                        matchesSubject
                    );

                }
            );


        table.innerHTML = "";


        if (
            filtered.length === 0
        ) {

            table.parentElement.style.display =
                "none";


            if (emptyState) {

                emptyState.style.display =
                    "block";

            }

            return;

        }


        table.parentElement.style.display =
            "block";


        if (emptyState) {

            emptyState.style.display =
                "none";

        }


        filtered.forEach(
            function (file) {

                const row =
                    document.createElement(
                        "tr"
                    );


                row.innerHTML = `

                    <td>

                        <div class="file-name">

                            <div class="file-icon">

                                <i class="bi bi-file-earmark-pdf"></i>

                            </div>

                            ${escapeHTML(
                    file.title
                )}

                        </div>

                    </td>


                    <td>

                        <span class="badge">

                            ${escapeHTML(
                    file.subject
                )}

                        </span>

                    </td>


                    <td>

                        ${escapeHTML(
                    file.uploadedBy
                )}

                    </td>


                    <td>

                        ${formatDate(
                    file.date
                )}

                    </td>


                    <td>

                        ${Number(
                    file.size
                ).toFixed(2)} MB

                    </td>


                    <td>

                        <button
                            class="action-btn download-btn"
                            onclick="downloadFile(${file.id})"
                            title="Download">

                            <i class="bi bi-download"></i>

                        </button>


                        <button
                            class="action-btn delete-btn"
                            onclick="deleteFile(${file.id})"
                            title="Delete">

                            <i class="bi bi-trash"></i>

                        </button>

                    </td>

                `;


                table.appendChild(
                    row
                );

            }
        );

    }

    catch (error) {

        console.error(
            "Files error:",
            error
        );

    }

}


/* =========================================
   UPLOAD
========================================= */

async function handleUpload(event) {

    event.preventDefault();


    const title =
        document.getElementById(
            "noteTitle"
        ).value.trim();


    const subject =
        document.getElementById(
            "noteSubject"
        ).value;


    const description =
        document.getElementById(
            "noteDescription"
        ).value.trim();


    const fileInput =
        document.getElementById(
            "noteFile"
        );


    const message =
        document.getElementById(
            "uploadMessage"
        );


    if (
        !fileInput.files.length
    ) {

        showMessage(
            message,
            "Please select a PDF file.",
            "error"
        );

        return;

    }


    const file =
        fileInput.files[0];


    if (
        file.type !==
        "application/pdf"

        &&

        !file.name
            .toLowerCase()
            .endsWith(".pdf")
    ) {

        showMessage(
            message,
            "Only PDF files are allowed.",
            "error"
        );

        return;

    }


    if (
        file.size >
        10 * 1024 * 1024
    ) {

        showMessage(
            message,
            "File must be smaller than 10 MB.",
            "error"
        );

        return;

    }


    const user =
        getCurrentUser();


    const formData =
        new FormData();


    formData.append(
        "title",
        title
    );


    formData.append(
        "subject",
        subject
    );


    formData.append(
        "description",
        description
    );


    formData.append(
        "uploadedBy",
        user.name || "Imad Khan"
    );


    formData.append(
        "file",
        file
    );


    try {

        showMessage(
            message,
            "Uploading...",
            "success"
        );


        const response =
            await fetch(
                `${API_URL}/api/files`,
                {

                    method: "POST",

                    body: formData

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Upload failed"
            );

        }


        showMessage(
            message,
            "Note uploaded successfully!",
            "success"
        );


        event.target.reset();


        const selected =
            document.getElementById(
                "selectedFile"
            );


        if (selected) {

            selected.textContent =
                "";

        }


        setTimeout(
            function () {

                window.location.href =
                    "files.html";

            },
            800
        );

    }

    catch (error) {

        showMessage(
            message,
            error.message,
            "error"
        );

    }

}


/* =========================================
   SELECTED FILE
========================================= */

function showSelectedFile(event) {

    const file =
        event.target.files[0];


    const container =
        document.getElementById(
            "selectedFile"
        );


    if (!file || !container)
        return;


    const size =
        (
            file.size /
            (1024 * 1024)
        ).toFixed(2);


    container.innerHTML = `

        <i class="bi bi-check-circle"></i>

        ${escapeHTML(
        file.name
    )}

        (${size} MB)

    `;

}


/* =========================================
   DOWNLOAD
========================================= */

function downloadFile(id) {

    window.open(
        `${API_URL}/api/files/${id}/download`,
        "_blank"
    );

}


/* =========================================
   DELETE
========================================= */

async function deleteFile(id) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this note?"
        );


    if (!confirmed)
        return;


    try {

        const response =
            await fetch(
                `${API_URL}/api/files/${id}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Delete failed"
            );

        }


        await renderFiles();

        await updateDashboard();

    }

    catch (error) {

        alert(
            error.message
        );

    }

}


/* =========================================
   SIDEBAR
========================================= */

function toggleSidebar() {

    const sidebar =
        document.getElementById(
            "sidebar"
        );


    if (sidebar) {

        sidebar.classList.toggle(
            "open"
        );

    }

}


/* =========================================
   THEME
========================================= */

function toggleTheme() {

    document.body.classList.toggle(
        "dark"
    );


    localStorage.setItem(
        "cloudnotes_theme",
        document.body.classList.contains(
            "dark"
        )
            ? "dark"
            : "light"
    );

}


function loadTheme() {

    const theme =
        localStorage.getItem(
            "cloudnotes_theme"
        );


    if (theme === "dark") {

        document.body.classList.add(
            "dark"
        );

    }

}


/* =========================================
   MESSAGE
========================================= */

function showMessage(
    element,
    message,
    type
) {

    if (!element)
        return;


    element.textContent =
        message;


    element.className =
        "message " + type;

}


/* =========================================
   DATE
========================================= */

function formatDate(date) {

    if (!date)
        return "-";


    return new Date(date)
        .toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );

}


/* =========================================
   BASIC HTML ESCAPING
========================================= */

function escapeHTML(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}