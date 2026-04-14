// Gym Analytics App - Frontend JS
// Handles UI, form submission, API communication, and dashboard data rendering
const API_BASE = "http://localhost:5000";
let queuedSets = [];
let activeUserId = null;


document.addEventListener('DOMContentLoaded', function() {
    initForms();
    initUI();
    prefillDateInputs();
    checkAuthStatus();
});


// ---------------------------------------------------------------------------
// UI Navigation
// ---------------------------------------------------------------------------

function newPage(shown, hidden) {
    document.getElementById(shown).style.display = 'block';
    document.getElementById(hidden).style.display = 'none';
    return false;
}

function logoutToStartup() {
    fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"}
    }).finally(() => {
        activeUserId = null;
        queuedSets = [];
        newPage('StartupPage', 'HomePage');
    });
    return false;
}


// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

function initForms() {
    // Login form
    document.getElementById('loginForm').addEventListener('submit', async e => {
        e.preventDefault();
        await handleLogin();
    });

    // Register step 1
    document.getElementById('registerFormStep1').addEventListener('submit', async e => {
        e.preventDefault();
        await handleRegisterStep1();
    });

    // Register step 2
    document.getElementById('registerFormStep2').addEventListener('submit', async e => {
        e.preventDefault();
        await handleRegisterStep2();
    });

    // Body metric form
    document.getElementById('bodyMetricForm').addEventListener('submit', async e => {
        e.preventDefault();
        await submitBodyMetric();
    });

    // Workout form
    document.getElementById('workoutForm').addEventListener('submit', async e => {
        e.preventDefault();
        await submitWorkout();
    });

    // Add set button
    document.getElementById('addSetBtn').addEventListener('click', () => addQueuedSet());

    // Refresh dashboard
    document.getElementById('refreshDashboardBtn').addEventListener('click', () => refreshDashboard());
}

function initUI() {
    // Setup chart instance
    window.volumeChart = new CanvasJS.Chart("myChart", {
        animationEnabled: true,
        theme: "light2",
        backgroundColor: "transparent",
        title: {text: "Total Volume over Time", fontColor: "#ffffff"},
        axisY: {labelFontColor: "#ffffff", lineColor: "rgba(255,255,255,0.2)"},
        axisX: {labelFontColor: "#ffffff", lineColor: "rgba(255,255,255,0.2)"},
        data: [{type: "column", dataPoints: []}]
    });
    window.volumeChart.render();
}

function prefillDateInputs() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('bodyMetricDate').value = today;
    document.getElementById('workoutDate').value = today;
}

async function checkAuthStatus() {
    try {
        const res = await fetch(`${API_BASE}/auth/me`, {credentials: "include"});
        if (res.ok) {
            const data = await res.json();
            activeUserId = data.user.id;
            newPage('HomePage', 'StartupPage');
            await refreshDashboard();
        }
    } catch (e) {}
}


// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

async function handleLogin() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;

    const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({username, password})
    });

    if (res.ok) {
        newPage('HomePage', 'LoginPage');
        await refreshDashboard();
    } else {
        alert("Invalid username or password");
    }
}

async function handleRegisterStep1() {
    const payload = {
        email: document.getElementById('registerEmail').value.trim(),
        username: document.getElementById('registerUsername').value.trim(),
        password: document.getElementById('registerPassword').value,
        confirmPassword: document.getElementById('registerPasswordConfirm').value
    };

    const res = await fetch(`${API_BASE}/auth/register/step1`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        const data = await res.json();
        activeUserId = parseInt(data.userId);
        newPage('InformationSection2', 'InformationSection');
    } else {
        const err = await res.json();
        alert(err.error || "Registration failed");
    }
}

async function handleRegisterStep2() {
    const payload = {
        userId: activeUserId,
        experienceLevel: document.getElementById('experienceLevel').value,
        programLengthWeeks: parseInt(document.getElementById('programLengthWeeks').value),
        targetWeeklySets: parseInt(document.getElementById('targetVolume').value),
        startingBodyweightKg: parseFloat(document.getElementById('startingBodyweight').value) || null,
        lifts: [
            {exerciseName: "Squat", bestWeightKg: parseFloat(document.getElementById('startingSquat').value) || 0, bestReps: 1},
            {exerciseName: "Bench Press", bestWeightKg: parseFloat(document.getElementById('startingBench').value) || 0, bestReps: 1},
            {exerciseName: "Deadlift", bestWeightKg: parseFloat(document.getElementById('startingDeadlift').value) || 0, bestReps: 1}
        ]
    };

    const res = await fetch(`${API_BASE}/auth/register/step2`, {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        newPage('HomePage', 'InformationSection2');
        await refreshDashboard();
    } else {
        const err = await res.json();
        alert(err.error || "Could not complete registration");
    }
}


// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

async function refreshDashboard() {
    try {
        const res = await fetch(`${API_BASE}/stats/dashboard-summary`, {credentials: "include"});
        if (!res.ok) return;
        const data = await res.json();
        renderDashboard(data.data);
    } catch (e) {}
}

function renderDashboard(d) {
    // Metric cards
    if (d.latestBodyMetrics?.bodyWeightKg)
        document.getElementById('metricBodyweight').textContent = `${d.latestBodyMetrics.bodyWeightKg} kg`;

    document.getElementById('metricWeeklyVolume').textContent = `${d.recentVolumeKg} kg`;

    if (d.bigThreePersonalBests.squat) {
        document.getElementById('metricSquatPb').textContent = `${d.bigThreePersonalBests.squat.weightKg} kg`;
        document.getElementById('metricSquatE1rm').textContent = `e1RM ${d.bigThreePersonalBests.squat.estimated1RMKg}`;
    }
    if (d.bigThreePersonalBests.bench) {
        document.getElementById('metricBenchPb').textContent = `${d.bigThreePersonalBests.bench.weightKg} kg`;
        document.getElementById('metricBenchE1rm').textContent = `e1RM ${d.bigThreePersonalBests.bench.estimated1RMKg}`;
    }
    if (d.bigThreePersonalBests.deadlift) {
        document.getElementById('metricDeadliftPb').textContent = `${d.bigThreePersonalBests.deadlift.weightKg} kg`;
        document.getElementById('metricDeadliftE1rm').textContent = `e1RM ${d.bigThreePersonalBests.deadlift.estimated1RMKg}`;
    }

    document.getElementById('metricCycleProgress').textContent =
        `Week ${d.cycleProgress.macroWeek} / ${d.cycleProgress.totalWeeks}`;
    document.getElementById('metricCycleBlock').textContent =
        `${d.volumeRecommendation.phase}`;

    // Volume chart
    fetch(`${API_BASE}/stats/volume`, {credentials: "include"})
        .then(r => r.ok ? r.json() : {data: []})
        .then(r => {
            const points = r.data.slice(-28).map(p => ({label: p.date, y: p.totalVolumeKg}));
            window.volumeChart.options.data[0].dataPoints = points;
            window.volumeChart.render();
        });
}


// ---------------------------------------------------------------------------
// Body Metrics
// ---------------------------------------------------------------------------

async function submitBodyMetric() {
    const payload = {
        recordedAt: document.getElementById('bodyMetricDate').value,
        bodyWeightKg: parseFloat(document.getElementById('bodyweightInput').value) || null,
        bodyFatPercent: parseFloat(document.getElementById('bodyfatInput').value) || null,
        waistCm: parseFloat(document.getElementById('waistInput').value) || null,
        chestCm: parseFloat(document.getElementById('chestInput').value) || null,
        armCm: parseFloat(document.getElementById('armsInput').value) || null,
        thighCm: parseFloat(document.getElementById('thighsInput').value) || null,
        notes: document.getElementById('bodyMetricNotes').value.trim()
    };

    await fetch(`${API_BASE}/stats/body-metrics`, {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    document.getElementById('bodyMetricForm').reset();
    prefillDateInputs();
    await refreshDashboard();
}


// ---------------------------------------------------------------------------
// Workout Logging
// ---------------------------------------------------------------------------

function addQueuedSet() {
    const set = {
        exerciseName: document.getElementById('setExercise').value,
        variationName: document.getElementById('setVariation').value.trim(),
        movementCategory: document.getElementById('setMovementCategory').value,
        setType: document.getElementById('setType').value,
        weightKg: parseFloat(document.getElementById('setWeight').value),
        reps: parseInt(document.getElementById('setReps').value),
        rpe: parseFloat(document.getElementById('setRpe').value) || null,
        rir: parseInt(document.getElementById('setRir').value) || null
    };

    if (!set.weightKg || !set.reps) return;

    queuedSets.push(set);
    renderQueuedSets();

    document.getElementById('setWeight').value = "";
    document.getElementById('setReps').value = "";
    document.getElementById('setRpe').value = "";
    document.getElementById('setRir').value = "";
}

function renderQueuedSets() {
    const container = document.getElementById('queuedSets');
    document.getElementById('queuedSetCount').textContent = `${queuedSets.length} sets queued`;
    container.innerHTML = queuedSets.map((s, i) => `
        <div class="metric-chip">
            <span>${s.exerciseName} | ${s.weightKg} kg × ${s.reps}</span>
            <button onclick="queuedSets.splice(${i},1); renderQueuedSets();" style="background:none; border:none; color:white; padding:0; min-height:0;">✕</button>
        </div>
    `).join("");
}

async function submitWorkout() {
    if (queuedSets.length === 0) return;

    const payload = {
        performedAt: document.getElementById('workoutDate').value,
        sets: queuedSets
    };

    await fetch(`${API_BASE}/stats/workout`, {
        method: "POST",
        credentials: "include",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
    });

    queuedSets = [];
    renderQueuedSets();
    document.getElementById('workoutForm').reset();
    prefillDateInputs();
    await refreshDashboard();
}