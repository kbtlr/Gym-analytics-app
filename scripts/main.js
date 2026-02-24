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
var char = new CanvasJS.Chart("myChart", {
    animationEnabled: true,
    theme: "light2",
    title:{
        text: "Volume by Week"
    },
    data: [{
        type: "column",
        indexLabelFontSize: 16,
        dataPoints: [  
            { label: "Week 1", y: 10000 },
            { label: "Week 2", y: 12000 },
            { label: "Week 3", y: 15000 },
        ]
    }]
});
