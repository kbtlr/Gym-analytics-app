//js file to sort interactions involving click behaviour, UI changes,
// and data fetching for the web application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initUIComponents();});

function initUIComponents() {
    // Add event listener to the button to navigate to the information page
    const startButton = document.querySelector('button');
    if (startButton) {
        startButton.addEventListener('click', toInfoPage);
    }
}
function newPage(shown, hidden) {
    document.getElementById(shown).style.display='block';
    document.getElementById(hidden).style.display='none';
    return false;
}