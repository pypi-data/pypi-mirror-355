// Security headers to pass in RPC API requests.
const headers = {};
// Map of input name to get value function for "Try it out" modal forms.
const formFunctions = {};

function isDark() {
    return localStorage.theme === "dark" || !("theme" in localStorage);
}

function copyToClipboard(codeId) {
    const code = document.getElementById(`${codeId}-code`);
    const copyTooltip = document.getElementById(`${codeId}-copy-tooltip`);
    const copiedTooltip = document.getElementById(`${codeId}-copied-tooltip`);
    copyTooltip.classList.toggle("hidden");
    copiedTooltip.classList.toggle("group-hover:opacity-100");
    // noinspection JSIgnoredPromiseFromCall
    navigator.clipboard.writeText(code.innerText);
    setTimeout(() => {
        copyTooltip.classList.toggle("hidden");
        copiedTooltip.classList.toggle("group-hover:opacity-100");
    }, 1250);
}

function onCopyMouseOver(copyId) {
    const copyTooltip = document.getElementById(`${copyId}-copy-tooltip`);
    copyTooltip.classList.toggle("group-hover:opacity-100");
}

function onMethodTitleBarOver(methodId) {
    const methodDiv = document.getElementById(`method-list-entry-${methodId}`);
    methodDiv.classList.add(
        "shadow-lg",
        "hover:bg-neutral-50",
        "hover:dark:bg-neutral-700",
    );
}

function onMethodTitleBarLeave(methodId) {
    const methodDiv = document.getElementById(`method-list-entry-${methodId}`);
    methodDiv.classList.remove(
        "shadow-lg",
        "hover:bg-neutral-50",
        "hover:dark:bg-neutral-700",
    );
}

function closeModal(modalId) {
    document.getElementById("dim-overlay").classList.add("hidden");
    document.body.style.overflow = "auto";
    document.getElementById(modalId).close();
}

function openModal(modalId, focusId) {
    document.getElementById(modalId).show();
    document.getElementById("dim-overlay").classList.remove("hidden");
    document.body.style.overflow = "hidden";
    if (focusId) {
        document.getElementById(focusId).focus();
    }
}

function toggleSchemaProperties(schemaId) {
    const propertiesElement = document.getElementById(`props-${schemaId}`);
    const toggleButton = document.getElementById(`toggle-${schemaId}`);

    if (propertiesElement.classList.contains("hidden")) {
        toggleButton.textContent = "⮟";
    } else {
        toggleButton.textContent = "⮞";
    }
    propertiesElement.classList.toggle("hidden");
}

function callMethod(methodId, params) {
    const responseField = document.getElementById(`${methodId}-response`);
    const responseLabel = document.getElementById(`${methodId}-response-label`);
    const responseDiv = document.getElementById(`${methodId}-response-div`);
    const spinner = document.getElementById(`${methodId}-spinner`);
    const callBtn = document.getElementById(`${methodId}-call-btn`);

    responseDiv.classList.add("hidden");
    spinner.classList.remove("hidden");
    callBtn.disabled = true;

    const data = { id: 1, method: methodId, params: params, jsonrpc: "2.0" };

    const options = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    };
    if (headers) {
        for (const key in headers) {
            options.headers[key] = headers[key];
        }
    }

    const apiUrlInput = document.getElementById("api-url-input");
    const url = `rpc-api?api-url=${apiUrlInput.value}`;

    fetch(url, options)
        .then((response) => response.json())
        .then((data) => {
            let text;
            if (data["result"] !== undefined) {
                text = JSON.stringify(data["result"], null, 2);
                responseLabel.textContent = "Result";
                responseLabel.classList.remove(
                    "text-red-600",
                    "dark:text-red-500",
                );
                responseLabel.classList.add(
                    "text-green-600",
                    "dark:text-green-500",
                );
            } else {
                text = JSON.stringify(data["error"]["message"], null, 2);
                if (data["error"]["data"]) {
                    text += "\n" + data["error"]["data"];
                }
                responseLabel.textContent = `Error: ${data["error"]["code"]}`;
                responseLabel.classList.remove(
                    "text-green-600",
                    "dark:text-green-500",
                );
                responseLabel.classList.add(
                    "text-red-600",
                    "dark:text-red-500",
                );
            }
            responseField.textContent = text === null ? "null" : text;
        })
        .catch((error) => {
            responseLabel.textContent = "Error";
            responseLabel.classList.remove("text-green-600");
            responseLabel.classList.add("text-red-600");
            responseField.textContent = error;
        })
        .finally(() => {
            spinner.classList.add("hidden");
            responseDiv.classList.remove("hidden");
            callBtn.disabled = false;
            // noinspection JSUnresolvedReference
            hljs.highlightElement(responseField);
        });
}

function toggleMethodDetails(methodId) {
    const div = document.getElementById(`method-${methodId}-div`);
    const symbol = document.getElementById(`method-${methodId}-symbol`);

    if (div.classList.contains("hidden")) {
        symbol.textContent = "⮟";
    } else {
        symbol.textContent = "⮞";
        const currentUrl = globalThis.location.href;
        const newUrl = currentUrl.split("#")[0];
        // Without timeout has is removed then instantly set.
        setTimeout(
            () => globalThis.history.replaceState({}, document.title, newUrl),
            10,
        );
    }
    div.classList.toggle("hidden");
}

function toggleMethodFromHash() {
    if (globalThis.location.hash) {
        const methodId = globalThis.location.hash.slice(1).replace(
            "method-",
            "",
        );
        const methodEntry = document.getElementById(`method-${methodId}-div`);
        if (!methodEntry) return;
        toggleMethodDetails(methodId);
        document.getElementById(`method-${methodId}-title-bar`)
            .scrollIntoView();
    }
}

function toggleTheme() {
    const themeIcon = document.getElementById("theme-icon");
    const codeTheme = document.getElementById("codeTheme");
    if (isDark()) {
        localStorage.theme = "light";
        document.documentElement.classList.remove("dark");
        themeIcon.textContent = "light_mode";
        codeTheme.href = "/static/vs.min.css";
    } else {
        localStorage.theme = "dark";
        document.documentElement.classList.add("dark");
        themeIcon.textContent = "dark_mode";
        codeTheme.href = "/static/vs2015.min.css";
    }
}

function setUrlStorage() {
    const apiUrlInput = document.getElementById("api-url-input");
    localStorage.setItem("api-url", apiUrlInput.value);
}

function filterFromQueryParams() {
    const searchParams = new URLSearchParams(globalThis.location.search);
    searchParams.forEach((_, v) => {
        try {
            document.getElementById(`tag-${v}-div`).classList.toggle("hidden");
            document.getElementById(`tag-${v}-option`).classList.toggle(
                "hidden",
            );
        } catch (_error) {
            // If API input is enabled rpc data will be absent on
            // initial request, there will be no tags, but we want to
            // keep the query params as they are and do nothing.
        }
    });
    applyFilters();
}

function onTagSelectChange() {
    const filterTagValue = document.getElementById("tag-filter-select").value;
    const defaultOption = document.getElementById("default-filter-option");
    defaultOption.selected = true;
    toggleTag(filterTagValue);
}

function toggleTag(filterTagValue) {
    document.getElementById(`tag-${filterTagValue}-div`).classList.toggle(
        "hidden",
    );
    document.getElementById(`tag-${filterTagValue}-option`).classList.toggle(
        "hidden",
    );

    // Adjust query params.
    const searchParams = new URLSearchParams(globalThis.location.search);
    if (searchParams.get(filterTagValue)) {
        searchParams.delete(filterTagValue);
    } else {
        searchParams.set(filterTagValue, "true");
    }
    history.pushState(
        {},
        "",
        globalThis.location.pathname + "?" + searchParams.toString(),
    );
    applyFilters();
}

function applyFilters() {
    const elements = document.querySelectorAll("[id^='method-tags-']");
    const allListEntries = document.querySelectorAll(
        "[id^='method-list-entry-']",
    );
    const searchParams = new URLSearchParams(globalThis.location.search);

    const hidden = [];
    searchParams.forEach((_, v) => {
        for (const element of elements) {
            const method = element.id.replace("method-tags-", "");
            const methodListEntry = document.getElementById(
                `method-list-entry-${method}`,
            );
            const methodTags = [];
            for (const child of element.children) {
                methodTags.push(child.innerHTML);
            }
            if (!methodTags.includes(v)) {
                hidden.push(methodListEntry);
                methodListEntry.classList.add("hidden");
            }
        }
    });

    for (const element of allListEntries) {
        if (!hidden.includes(element)) {
            element.classList.remove("hidden");
        }
    }
}

function onInputTypeChange(schemaId, idx, numItems) {
    document.getElementById(`${schemaId}_${idx}-form`).classList.remove(
        "hidden",
    );
    for (let i = 0; i < numItems; i++) {
        if (i === idx) {
            continue;
        }
        try {
            document.getElementById(`${schemaId}_${i}-form`).classList.add(
                "hidden",
            );
        } catch (_e) {
            // Element won't exist if it's a recursive schema that
            // hasn't been fetched yet.
        }
    }
}

function upItemCounter(inputId, min, max) {
    const counter = document.getElementById(`item-${inputId}-counter`);
    counter.value = Number(counter.value) + 1;
    determineItemButtonDisabled(inputId, min, max);
}

function removeItem(inputId, min, max) {
    const counter = document.getElementById(`item-${inputId}-counter`);
    const itemDiv = document.getElementById(
        `input-${inputId}_item${Number(counter.value)}`,
    );
    itemDiv.remove();
    counter.value = Number(counter.value) - 1;
    determineItemButtonDisabled(inputId, min, max);
}

function determineItemButtonDisabled(inputId, min, max) {
    const counter = document.getElementById(`item-${inputId}-counter`);
    const addBtn = document.getElementById(`${inputId}-add-item-btn`);
    const removeBtn = document.getElementById(`${inputId}-remove-item-btn`);
    const numItems = Number(counter.value);

    removeBtn.disabled = numItems <= min;
    if (max !== null) {
        addBtn.disabled = numItems >= max;
    }
}

function toggleInput(inputId) {
    const input = document.getElementById(`${inputId}-input-span`);
    const checkbox = document.getElementById(`${inputId}-enabled`);
    if (checkbox.checked) {
        input.classList.remove("hidden");
    } else {
        input.classList.add("hidden");
    }
}

function getInputFunction(inputId, func) {
    const input = document.getElementById(`${inputId}-input-span`);
    if (input.classList.contains("hidden")) {
        return undefined;
    } else {
        return func();
    }
}

function toggleMethodCallDetails(count) {
    const methodCallDetails = document.getElementById(
        `method-call-details-${count}`,
    );
    const icon = document.getElementById(`monitor-icon-${count}`);
    const header = document.getElementById(`monitor-header-${count}`);
    methodCallDetails.classList.toggle("hidden");
    icon.classList.toggle("rotate-90");
    header.classList.toggle("rounded-b-3xl");
}
