document.addEventListener("DOMContentLoaded", function () {
  let tasks = {};
  let calendar;

  // 🎨 Define colors based on priority and done state
  function getColor(task) {
    if (task.done) return "#b2bec3"; // gray if done
    switch (task.priority) {
      case 1: return "#ff7675";
      case 2: return "#fdcb6e";
      case 3: return "#55efc4";
      default: return "#dfe6e9";
    }
  }

  // 🟢 Handle click (toggle done / undone)
  async function handleEventClick(info) {
    const person = document.getElementById("personDropdown").value;
    const title = info.event.title.replace("✅ ", "");
    const target = tasks[person].find(t => t.title === title || t.title === info.event.title);

    if (!target) return alert("Task not found in memory!");

    if (!target.done) {
      if (confirm(`Mark "${title}" as done?`)) {
        target.done = true;
        info.event.setProp("color", getColor(target));
        info.event.setProp("title", "✅ " + title);
      }
    } else {
      if (confirm(`Undo "${title}" and mark as not done?`)) {
        target.done = false;
        info.event.setProp("color", getColor(target));
        info.event.setProp("title", title.replace("✅ ", ""));
      }
    }

    await saveUpdatedTasks();
  }

  // 🧩 Initialize the calendar
  function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'timeGridWeek',
      locale: 'en',
      allDaySlot: false,
      slotMinTime: "08:00:00",
      slotMaxTime: "20:00:00",
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek,timeGridDay'
      },
      eventDisplay: 'block',
      eventClick: handleEventClick,
      events: []
    });
    calendar.render();
  }

  // 👀 Show selected employee’s tasks
  function showPersonTasks(person) {
    if (!tasks[person]) return;
    const userTasks = tasks[person].map(task => ({
      title: (task.done ? "✅ " : "") + task.title,
      start: task.start,
      end: task.end,
      color: getColor(task)
    }));
    calendar.removeAllEvents();
    calendar.addEventSource(userTasks);
  }

  // 🔽 Dropdown builder
  function buildDropdown() {
    const dropdown = document.getElementById("personDropdown");
    dropdown.innerHTML = "";
    Object.keys(tasks).forEach(person => {
      const option = document.createElement("option");
      option.value = person;
      option.textContent = person;
      dropdown.appendChild(option);
    });
    dropdown.addEventListener("change", (e) => {
      showPersonTasks(e.target.value);
    });
    dropdown.value = Object.keys(tasks)[0];
    dropdown.dispatchEvent(new Event('change'));
  }

  // 📥 Load schedule.json from Flask
  async function loadTasks() {
    try {
      const res = await fetch("http://127.0.0.1:5501/get_tasks");
      if (!res.ok) throw new Error("Failed to load JSON");
      tasks = await res.json();
      console.log("✅ Loaded latest schedule.json");

      if (!calendar) {
        initCalendar();
        buildDropdown();
      }
      const dropdown = document.getElementById("personDropdown");
      showPersonTasks(dropdown.value || Object.keys(tasks)[0]);
    } catch (err) {
      console.error("Error loading schedule:", err);
    }
  }

  // 💾 Save updated JSON back to Flask
  async function saveUpdatedTasks() {
    try {
      const res = await fetch("http://127.0.0.1:5501/update_task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tasks)
      });
      const data = await res.json();
      if (data.status === "success") {
        console.log("✅ schedule.json updated successfully!");
      }
    } catch (err) {
      console.error("❌ Failed to update schedule:", err);
    }
  }

  // 🚀 Start auto-refresh
  loadTasks();
  setInterval(loadTasks, 5000);
});