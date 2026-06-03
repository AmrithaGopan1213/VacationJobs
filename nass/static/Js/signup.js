// Function to validate the form
function validateForm(event) {
    event.preventDefault();  
    
    // Get form elements
    const firstname = document.getElementById('firstname');
    const email = document.getElementById('email');
    const phonenumber = document.getElementById('phonenumber');
    const username = document.getElementById('username');
    const password = document.getElementById('password');
    const cpassword = document.getElementById('cpassword');

    // Error message elements
    const firstnameError = document.getElementById('firstname-error');
    const emailError = document.getElementById('email-error');
    const phonenumberError = document.getElementById('phonenumber-error');
    const usernameError = document.getElementById('username-error');
    const passwordError = document.getElementById('password-error');
    const confirmPasswordError = document.getElementById('confirm-password-error');

    let isValid = true;

    // Reset error messages
    firstnameError.style.display = 'none';
    emailError.style.display = 'none';
    phonenumberError.style.display = 'none';
    usernameError.style.display = 'none';
    passwordError.style.display = 'none';
    confirmPasswordError.style.display = 'none';

    // Firstname validation: Only letters allowed
    const namePattern = /^[A-Za-z]+$/;
    if (!namePattern.test(firstname.value)) {
        firstnameError.style.display = 'inline';
        isValid = false;
    }

    // Email validation: Basic format check
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email.value)) {
        emailError.style.display = 'inline';
        isValid = false;
    }

    // Phone number validation: Only digits allowed
    const phonePattern = /^[0-9]+$/;
    if (!phonePattern.test(phonenumber.value)) {
        phonenumberError.style.display = 'inline';
        isValid = false;
    }

    // Username validation: Only letters allowed
    if (!namePattern.test(username.value)) {
        usernameError.style.display = 'inline';
        isValid = false;
    }

    // Password validation: Only numbers allowed (according to your specification)
    const passwordPattern = /^[0-9]+$/;
    if (!passwordPattern.test(password.value)) {
        passwordError.style.display = 'inline';
        isValid = false;
    }

    // Confirm password validation: Match passwords
    if (password.value !== cpassword.value) {
        confirmPasswordError.style.display = 'inline';
        isValid = false;
    }

    // If form is valid, submit it
    if (isValid) {
        document.getElementById('registration-form').submit();
    }
}

// for going to next input after Enter 

document.addEventListener('DOMContentLoaded',()=>{
    const inputs = document.querySelectorAll('input');

    inputs.forEach((input,index)=>{
        input.addEventListener('keydown',(event)=>{
            if (event.key ==='Enter'){
                event.preventDefault();
                const nextInput = inputs[index + 1];
                if (nextInput){
                    nextInput.focus();
                }
            }
        })
    });
});