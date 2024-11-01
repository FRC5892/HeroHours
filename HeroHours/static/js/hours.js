// load it all at the beginning, to keep checkins fast
const successAudio = new Audio(successAudioUrl);
const notFoundAudio = new Audio(notFoundAudioUrl);
const outAudio = new Audio(outAudioUrl);


function playSound(status) {
  console.debug("Playing Sound");
  return new Promise((resolve) => {
    let audio = null;

    switch (status) {
      case "Success":
        audio = successAudio;
        break;
      case "User Not Found":
        audio = notFoundAudio;
        break;
      case "Check Out":
        audio = outAudio;
        break;
      default:
        resolve(); // No audio for other statuses
        return;
    }
    audio.currentTime = 0;
    audio
      .play()
      .then(() => {
        // Wait for the audio to finish playing
        audio.onended = function () {
            console.debug("audio ended")
          resolve(); // Resolve the promise after the audio finishes
        };
      })
      .catch(function (error) {
        console.error("Audio playback failed:", error);
        resolve(); // Resolve even if audio playback fails
      });
  });
}

window.addEventListener("online", function () {
  document.getElementById("status").hidden = true;
});
window.addEventListener("offline", function () {
  document.getElementById("status").hidden = false;
});
window.onload = function () {
  document.getElementById("userID").focus();
};

function updateTime() {
  const timeDiv = document.querySelector(".time");
  const now = new Date();
  const prehours = now.getHours() == 12? 12 : now.getHours() % 12;
  const hours = prehours.toString().padStart(2, "0");
  const minutes = now.getMinutes().toString().padStart(2, "0");
  const seconds = now.getSeconds().toString().padStart(2, "0");
  let half = now.getHours() >= 12 ? "PM" : "AM";

  timeDiv.textContent = `${
    now.getMonth() + 1
  }/${now.getDate()}/${now.getFullYear()} 
   ${hours}:${minutes}:${seconds} ${half}`;
}

// Update time every second
setInterval(updateTime, 1000);

document.addEventListener("DOMContentLoaded", function (event) {
  // Initial time update
  updateTime();

  // handle form submission
  document
    .querySelector("#subID")
    .addEventListener("submit", handleFormSubmission);
  // prevent the user from ever loosing focus on the input
  document.querySelector("#userID").addEventListener("blur", function (event) {
    setTimeout(function () {
      event.target.focus();
    }, 10);
  });
});

async function handleFormSubmission(event) {
  console.time('benchmark');
  let serialized_data = new URLSearchParams(new FormData(this)).toString();
  let data = serialized_data.split("&")[1].split("=")[1];
  if (data == "-404" || data == "%2B404" || data == "*"||data == 'admin') {
    // let html5 handle it & reload the whole page
    return;
  }
  // send the request in the background
  event.preventDefault(); // Prevent the default form submission
  // check for only whitespace
  if (!/\S/.test(decodeURI(data))) {
    document.getElementById("subID").reset(); // reset the input box
    return;
  }
  // submit the form ourselves
  const req = await fetch(queryUrl, {
    headers: {
      "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
      'X-Requested-With': 'XMLHttpRequest'
    },
    body: serialized_data.toString(),
    method: "POST",
  }).then(async function (response) {
    console.log(response)
    console.timeLog('benchmark');
    //handle the form response ourselves
    document.getElementById("subID").reset(); // reset the input box
    if (response.ok) {
      console.log(new Date())
      console.debug(response);
      // read the body
      let body = await response.json();
      console.debug(body);
      if (body.status == "Sent") return;
      // Play the sound based on the response
      playSound(body.status);
      // update the color of the user effected
      if (body.state != null) {
        document.getElementById(body.newlog.user).className = body.state
          ? "member checkedIn"
          : "member ";
      }
      // add it to the log
      addRow(body.newlog);
      // update check in count
      document.getElementById("num-in").innerHTML = `${body.count} Checked In`;
    } else {
      console.error("Error:", response);
      addRow({
        id: 0,
        userID: data,
        operation: "None",
        status: response.statusText,
        message: "",
      });
    }
  });
  console.timeEnd('benchmark');
}

async function addRow(item) {
  console.log(item);
  // Get the table body
  let table = document.getElementById("logBody");
  let colorClass;
  let operationClass;
  console.log(item);
  switch (item.status) {
    case "User Not Found":
      colorClass = "warning";
      operationClass = colorClass;
      break;
    case "Success":
      colorClass = "success";
      switch (item.operation) {
        case "Check In":
          operationClass = "success";
          break;
        case "Check Out":
          operationClass = "check-out";
          break;
        default:
          operationClass = "success";
      }
      break;
    default:
      colorClass = "error";
      operationClass = colorClass;
  }
  let backgroundClass = colorClass + " bg";

  // Insert a new row at the top
  let newRow = table.insertRow(0);
  newRow.className = backgroundClass;

  // Create and append the first cell (UserID)
  let cell1 = newRow.insertCell(0);
  cell1.innerHTML = item.entered;

  // Create and append the second cell (Operation)
  let cell2 = newRow.insertCell(1);

  // Since we are adding to the log, flash the top of the screen to let the user know something is done
  document.querySelector(".controls").className = "controls " + operationClass;
  setTimeout(function () {
    document.querySelector(".controls").className = "controls";
  }, 500);

  cell2.innerHTML = `<span class="${operationClass} label">${item.operation}</span>`;

  // Create and append the third cell (Status and Message)
  let cell3 = newRow.insertCell(2);
  cell3.innerHTML = `<span class="${colorClass} label">${item.status}&nbsp;${item.message}</span>`;
}
