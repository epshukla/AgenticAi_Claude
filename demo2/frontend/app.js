
function initApp() {
    console.log("App initializing...");

    const user_name = "Guest";
    // Error: Assignment to constant variable
    user_name = "Admin";

    if (true) {
        var x = 10;
    }
    // Minor issue: 'x' usage outside block (var scoping issues, but technically valid JS, heavily discouraged)
    console.log(x);

    alert("Welcome " + user_name) // Error: Missing semicolon
}

initApp();
