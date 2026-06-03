
 // Function to trigger the file input click
 function triggerFileUpload() {
    document.getElementById("fileUpload").click();
}

// Function to preview the uploaded profile photo
function previewProfilePhoto() {
    const file = document.getElementById("fileUpload").files[0];
    const reader = new FileReader();

    reader.onloadend = function () {
        document.getElementById("profilePhoto").src = reader.result;
    };

    if (file) {
        reader.readAsDataURL(file);
    }else {
        alert("No file selected or invalid file type!");
    }
}


// Fetch and display saved languages
const fetchLanguages = () => {
    fetch("/languages/", { method: "GET" })
    .then((response) => response.json())
    .then((data) => {
    renderLanguageList(data.languages || []);
    })
    .catch((error) => console.error("Error:", error));
    };

const renderLanguageList = (languages) => {
    const languageList = document.getElementById("languageList");
    languageList.innerHTML = ""; // Clear the list
    languages.forEach(({ language, proficiencies }, index) => {
    const listItem = document.createElement("div");
    listItem.innerHTML = `
    <strong>${language}</strong>: ${proficiencies.join(", ")}
    <button onclick="deleteLanguage(${index})">❌</button>
    `;
    languageList.appendChild(listItem);
    });
    };

// Add a language
document.getElementById("addLanguage").addEventListener("click", () => {
    const language = document.getElementById("language").value;
    const checkboxes = document.querySelectorAll('input[name="proficiency"]:checked');
    const proficiencies = Array.from(checkboxes).map((cb) => cb.value);

    if (language && proficiencies.length) { 
    fetch("/languages/", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ language, proficiency: proficiencies }),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.message) {
        renderLanguageList(data.languages);
        document.getElementById("language").value = "";
        checkboxes.forEach((cb) => (cb.checked = false));
        } else {
        alert(data.error || "Failed to add language.");
        }
    })
    .catch((error) => console.error("Error:", error));
    } else {
    alert("Please enter a language and select at least one proficiency.");
    }
    });

// Delete a language
const deleteLanguage = (index) => {
    fetch("/languages/", {
    method: "DELETE",
    headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ index }),
    })
    .then((response) => response.json())
    .then((data) => {
    if (data.message) {
        renderLanguageList(data.languages);
    } else {
        alert(data.error || "Failed to delete language.");
    }
    })
    .catch((error) => console.error("Error:", error));
    };

// Initial fetch of languages
fetchLanguages();

// Fetch the languages and populate the dropdown
fetch('/api/languages/')
    .then(response => response.json())
    .then(data => {
        const dropdown = document.getElementById("language");
        data.all_languages.forEach(language => {
            const option = document.createElement("option");
            option.value = language;
            option.textContent = language;
            dropdown.appendChild(option);
        });
    })
    .catch(error => console.error("Error fetching languages:", error));


document.addEventListener("DOMContentLoaded", function () {
    

    const countrySelect = document.getElementById("country");
    const stateSelect = document.getElementById("state");
    const citySelect = document.getElementById("city");

    // API URLs
    const API_URL = 'https://api.countrystatecity.in/v1'; 
    const API_KEY = 'elRvTUp5ZkpBUEJRRHhrWEluZDFEcXBua0xqdGRPckMwZThPQWxVOA=='; 
    const headers = { 'X-CSCAPI-KEY': API_KEY };

    // Populate countries
    fetch(`${API_URL}/countries`, { headers })
        .then(response => response.json())
        .then(countries => {
            countrySelect.innerHTML = '<option value="">Select Country</option>';
            countries.forEach(country => {
                const option = new Option(country.name, country.iso2);
                if (country.iso2 === savedCountry) option.selected = true;
                countrySelect.add(option);
            });

            // Trigger state dropdown population if a country is saved
            if (savedCountry) {
                populateStates(countrySelect.value);
            }
        });

// Populate states based on selected country
function populateStates(countryCode) {
    fetch(`${API_URL}/countries/${countryCode}/states`, { headers })
        .then(response => response.json())
        .then(states => {
            stateSelect.innerHTML = '<option value="">Select State</option>';
            states.forEach(state => {
                const option = new Option(state.name, state.iso2);
                if (state.iso2 === savedState) option.selected = true;
                stateSelect.add(option);
            });

            // Trigger city dropdown population if a state is saved
            if (savedState) {
                populateCities(countryCode, stateSelect.value);
            }
        });
}

// Populate cities based on selected state
function populateCities(countryCode, stateCode) {
    fetch(`${API_URL}/countries/${countryCode}/states/${stateCode}/cities`, { headers })
        .then(response => response.json())
        .then(cities => {
            citySelect.innerHTML = '<option value="">Select City</option>';
            cities.forEach(city => {
                const option = new Option(city.name, city.name);
                if (city.name === savedCity) option.selected = true;
                citySelect.add(option);
            });
        });
}

// Event listeners for dynamic population
countrySelect.addEventListener("change", function () {
    populateStates(this.value);
    stateSelect.innerHTML = '<option value="">Select State</option>';
    citySelect.innerHTML = '<option value="">Select City</option>';
});

stateSelect.addEventListener("change", function () {
    populateCities(countrySelect.value, this.value);
    citySelect.innerHTML = '<option value="">Select City</option>';
});
});


// Hobbies Drop Down

let selectedHobbies =hobbys.trim() ? hobbys.split(",") : [];
const dropdown = document.getElementById("dropdown-body");

function toggleDropdown() {
    dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
}

document.addEventListener("click", (event) => {
    const header = document.querySelector(".combo-box-header");
    if (!dropdown.contains(event.target) && !header.contains(event.target)) {
        dropdown.style.display = "none";
    }
    });

function updateHobbies(checkbox) {
    const hobby = checkbox.value;

    if (checkbox.checked) {
        // Add hobby if maximum limit not reached
        if (selectedHobbies.length < 3) {
            selectedHobbies.push(hobby);
        } else {
            checkbox.checked = false; // Prevent exceeding limit
            alert("You can select a maximum of 3 hobbies.");
        }
    } else {
        // Remove hobby if unchecked
        selectedHobbies = selectedHobbies.filter((h) => h !== hobby);
    }
    display_hobbies();
    }

function display_hobbies(){

    // Display selected hobbies in the header
    const header = document.querySelector(".combo-box-header");
    header.textContent = selectedHobbies.length
        ? selectedHobbies.join(",")
        : "Select Your Hobbies upto 3";
    }

display_hobbies();

function saveHobbies() {
console.log("Selected hobbies:", selectedHobbies);

fetch("/save_hobbies/", {
    method: "POST",
    headers: { "Content-Type": "application/json","X-CSRFToken": getCookie("csrftoken"), },
    body: JSON.stringify({ hobbies: selectedHobbies }),
})
    .then((response) => {
    if (response.ok) {
        alert("Profile Saved Successfully")
        window.location.href = "/user/";
    } else {
        console.error("Failed to save hobbies.");
    }
})
    .then(data)

    .catch((error) => {
        console.error("Error saving hobbies:", error);
    });

}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}