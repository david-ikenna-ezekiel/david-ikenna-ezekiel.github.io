// Wait for the DOM to load
document.addEventListener("DOMContentLoaded", function () {
    // Select the navigation element and create a toggle button for mobile devices
    const nav = document.querySelector("nav");
    const navLinks = document.querySelector(".nav-links");
  
    // Create the mobile menu toggle button
    const toggleButton = document.createElement("div");
    toggleButton.classList.add("toggle-button");
    toggleButton.innerHTML = `<span></span><span></span><span></span>`;
    nav.insertBefore(toggleButton, navLinks);
  
    // Toggle the navigation menu on button click
    toggleButton.addEventListener("click", function () {
      nav.classList.toggle("active");
    });
  });
  