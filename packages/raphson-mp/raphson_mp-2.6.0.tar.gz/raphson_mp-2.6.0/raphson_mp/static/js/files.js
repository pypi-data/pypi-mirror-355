import { createIconButton, vars } from "./util.js";

function tdIconButton(button) {
    const td = document.createElement("td");
    td.classList.add('button-col');
    td.append(button);
    return td;
}

const uploadFilesButton = document.getElementById('upload-files-button');
if (uploadFilesButton) {
    uploadFilesButton.addEventListener('click', () => {
        uploadFilesButton.setAttribute("disabled", "");
        document.getElementById('upload-files-form').hidden = false;
    });
}

const createDirectoryButton = document.getElementById('create-directory-button');
if (createDirectoryButton) {
    createDirectoryButton.addEventListener('click', () => {
        createDirectoryButton.setAttribute("disabled", "");
        document.getElementById('create-directory-form').hidden = false;
    });
}

for (const tr of document.getElementById("tbody").children) {
    const path = tr.dataset.path;
    const name = path.split("/").slice(-1)[0];

    // download button
    const downloadButton = createIconButton('download');
    downloadButton.addEventListener('click', () => {
        window.open('/files/download?path=' + encodeURIComponent(path));
    });
    tr.append(tdIconButton(downloadButton));

    // rename button
    if (uploadFilesButton) { // presence of upload button means user has write permissions
        const renameButton = createIconButton('rename-box');
        renameButton.addEventListener('click', () => {
            window.location.assign('/files/rename?path=' + encodeURIComponent(path));
        });
        tr.append(tdIconButton(renameButton));

        // trash or restore button
        const isTrash = window.location.href.endsWith("&trash"); // TODO properly examine query string
        const trashButton = createIconButton(isTrash ? 'delete-restore' : 'delete');
        trashButton.addEventListener('click', async () => {
            const formData = new FormData();
            formData.append("csrf", vars.csrfToken);
            formData.append("path", path);
            formData.append("new-name", isTrash ? name.substring(".trash.".length) : `.trash.${name}`);
            await fetch('/files/rename', {method: 'POST', body: formData});
            location.reload();
        });
        tr.append(tdIconButton(trashButton));
    }
}
