const sheet = SpreadsheetApp.getActiveSpreadsheet();
const users = sheet.getSheetByName("User Logs");
const logs = sheet.getSheetByName("Activity Logs");
const test = sheet.getSheetByName("test");
const meetings = sheet.getSheetByName("Attendance By Meeting");

//insertAll is very slow and should not be run from or during the request, apps script does not yet support async functions properly

function doPost(e) {
let data = e.postData.contents.toString();
test.appendRow([data,new Date()]);
console.log(data);
 return ContentService.createTextOutput(JSON.stringify({"result": "success"}));
}

function addAll(){
  // Clear the sheets
  users.clear();
  logs.clear();

  // Fetch the last row and the data
  const last = test.getLastRow();
  const data = JSON.parse(test.getRange(`A${last}`).getValue());

  const userHeaders = [["Id", "Name", "Total Seconds", "Total Hours", "Last Check In", "Last Check Out", "Is Checked In?"]];
  const logHeaders = [["Log #", "ID", "operation", "status", "message", "timestamp"]];

  // Prepare data for the 'users' sheet
  const userRows = JSON.parse(data[0]).map(row => {
    const info = row.fields;
    return [row.pk, `${info.First_Name} ${info.Last_Name}`, info.Total_Seconds, info.Total_Hours, info.Last_In, info.Last_Out, info.Checked_In];
  });

  // Prepare data for the 'logs' sheet
  const logRows = JSON.parse(data[1]).map(row => {
    const info = row.fields;
    const splitTimestamp = info.timestamp.split("T");
    const splitDate = splitTimestamp[0].split("-");
    const day = splitDate[2]
    const month = splitDate[1]
    const year = splitDate[0]
    const time = splitTimestamp[1].split(".")[0]


    const propperTimespamp = month + "/" + day + "/" + year + " " + time
    return [row.pk, info.userID, info.operation, info.status, info.message, propperTimespamp];
  });

  // Write all data at once
  users.getRange(1, 1, userHeaders.length, userHeaders[0].length).setValues(userHeaders);
  if (userRows.length > 0) {
    users.getRange(2, 1, userRows.length, userRows[0].length).setValues(userRows);
  }

  logs.getRange(1, 1, logHeaders.length, logHeaders[0].length).setValues(logHeaders);
  if (logRows.length > 0) {
    logs.getRange(2, 1, logRows.length, logRows[0].length).setValues(logRows);
  }
}

function addMeeting(){
  meetings.insertColumns(1, 3);

  let date = new Date();
  console.log(('0'+(date.getMonth()+1)).slice(-2))
  let datestr = `${date.getFullYear()}-${('0'+(date.getMonth()+1)).slice(-2)}-${('0'+date.getDate()).slice(-2)}`;
  meetings.getRange('A1:B1').setValues([['Date:','Total:']]);
  meetings.getRange("A2").setValue(datestr);
  meetings.getRange("B2").setFormula(`=COUNTIF(A4:A,">0")`);
  meetings.getRange("A3:B3").setValues([["ID:","Name:"]]);
  meetings.getRange('A4').setFormula(`=query('Live Activity Logs'!$A$2:$F,"SELECT avg(A),F where E contains date '"&Text(A$2,"yyyy-mm-dd")&"' and F != '' and B != 'None' group by F label avg(A) '', F ''",0)`);
  meetings.getRange('C:C').setBackgroundColor("Black");

}


function onOpen() {
  SpreadsheetApp.getUi() // Or DocumentApp or SlidesApp or FormApp.
      .createMenu('Custom Functionality')
      .addItem("Update Logs","addAll")
      .addItem("Add Meeting For Attendance","addMeeting")
      .addToUi();
}