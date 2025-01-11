let username = document.getElementsByName("username")[0];
      username.disabled = true;
      username.required = false;
      username.autocomplete = "off"; 
      username.value = "";
      let password = document.getElementsByName("password")[0];
      password.focus();
      let firstTime = true;
      document
        .getElementsByTagName("form")[0]
        .addEventListener("submit", function (e) {
            //console.log(e);
          if (firstTime) {
            firstTime = false;
            e.preventDefault();
            let enteredpassword = password.value;
            let splitpassword = enteredpassword.split("\\");
            username.value = splitpassword[0];
            password.value = splitpassword[1];
            username.disabled = false;
            this.submit();
          }
        });
    function updateTime() {
        const timeDiv = document.querySelector(".time");
        const now = new Date();
        const prehours = now.getHours() % 12;
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

    window.addEventListener("online", function () {
        document.getElementById("status").hidden = true;
    });
    window.addEventListener("offline", function () {
        document.getElementById("status").hidden = false;
    });

    
    password.addEventListener("blur",onBlur);
    function onBlur(event) {
      setTimeout(function () {
      event.target.focus();
      }, 10);
    }
    document.querySelector("#usernameButton").addEventListener("click",(e)=>{
        //console.log(e);
      document.querySelector("#usernameButton").disabled = true;
      firstTime = false;
      username.disabled = false;
      username.required = true;
      username.autocomplete = "username"; 

      password.removeEventListener("blur",onBlur);
      username.focus();
    });
  document.addEventListener('keydown', function(event) {
    if( event.keyCode == 17 || event.keyCode == 74 )
      event.preventDefault();
  });
