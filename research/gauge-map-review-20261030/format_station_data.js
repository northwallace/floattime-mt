function setlinks(site) {

    //Clean up HTML when user toggles between sites
    document.getElementById("dayplot").innerHTML = "";
    document.getElementById("arcplot").innerHTML = "";
    document.getElementsByName("remove").innerText = "";
    var e = document.getElementsByName("remove")[0];
    e.innerHTML = e.innerHTML.replace('<br>', '');
    var e = document.getElementsByName("remove")[1];
    e.innerHTML = e.innerHTML.replace('<br>', '');
    var e = document.getElementsByName("remove")[2];
    e.innerHTML = e.innerHTML.replace('<br>', '');

    //Set up href links for daily and instant data
    var txt = site + " Daily Data";
    var a = document.getElementById('daily'); 
    document.getElementById('daily').textContent = txt;
    var link = "https://www.usbr.gov/gp-bin/hydromet_archives.pl?" + site;
    a.href = link;
    var txt = site + " Instant Data";
    var a = document.getElementById('inst'); 
    document.getElementById('inst').textContent = txt;
    var link = "https://www.usbr.gov/gp-bin/hydromet_dayfiles.pl?" + site;
    a.href = link;

    //Send site code to an API to pull in parameters
    loadselpararc(site,'ARCHIVE');
    loadselparday(site,'DAYFILE');
}

function processparameterday(plistday,site) {
    //Once we have parameters for instant/dayfile data- format the parameters in HTML
    //Create <ul> tag to house <li> 
    var ulist = document.createElement("UL");
    var id = "instantlist";
    ulist.id = id;
    document.getElementById("dayplot").appendChild(ulist);

    //Iterate through the parameter list to create <li> tags with links to parameter graphs
    plistday.forEach(function(parameterday) {
        //Create <li> tags for each parameter
        var list = document.createElement("LI");
        var code = parameterday.split(' ');
        var id = code[0] + "Instant";
        list.id = id;
        document.getElementById("instantlist").appendChild(list);
        //Create links for each paramters
        var link = document.createElement("A");
        link.innerText = parameterday;
        link.setAttribute("target", "_blank");
        code = parameterday.split(' ');
        link.href = "https://www.usbr.gov/gp-bin/hydromet_dayplt.pl?" + site + "&" + code[0];
        document.getElementById(id).appendChild(link);
    })
}

function processparameterarc(plist,site) {
    //Once we have parameters for daily/archive data- format the parameters in HTML
    //Create <ul> tag to house <li> 
    var ulist = document.createElement("UL");
    var id = "dailylist";
    ulist.id = id;
    document.getElementById("arcplot").appendChild(ulist);

    //Iterate through the parameter list to create <li> tags with links to parameter graphs
    plist.forEach(function(parameter) {
        //Create <li> tags for each parameter
        var list = document.createElement("LI");
        var code = parameter.split(' ');
        var id = code[0] + "Daily";
        list.id = id;
        document.getElementById("dailylist").appendChild(list);
        //Create links for each parameter
        var link = document.createElement("A");
        link.innerText = parameter;
        link.setAttribute("target", "_blank");
        code = parameter.split(' ');
        link.href = "https://www.usbr.gov/gp-bin/hydromet_arcplt.pl?" + site + "&" + code[0];
        document.getElementById(id).appendChild(link);
    })
}


//======================================================================
function loadselpararc(objsite,txtdb)
//* Primary handler for loading a specified select box with a parameter
//* list based on the changed value of a specified site text box. 
//----------------------------------------------------------------------
{ 
    var url = "https://www.usbr.gov/gp-bin/arccsv.pl?" + objsite + ",+";
    if (objsite.value == "") return ;	//--- if site is blank, bail out
    var cookiename = objsite.name;		//-- the cookie name is the site txtbox name
    if (navigator.cookieEnabled) document.cookie = "parstring="; //-- clear
    if (window.XMLHttpRequest) 	//--- other browsers
    { 
    var httpRequest = new XMLHttpRequest(); 
    } 
    else
    { 
    var httpRequest = new ActiveXObject("Microsoft.XMLHTTP"); 
    } 
  
    httpRequest.open("GET", url, true); //-- invoke url and wait for return
    httpRequest.onreadystatechange = function() {processRequestarc(objsite,txtdb,httpRequest); } ; 
    httpRequest.send(null); 
}

//======================================================================
function processRequestarc(objsite,txtdb,httpRequest) 
//* This is the call back method for the httpRequest state change event.
//* If the call is completed when the readyState is 4 and if the HTTP is 
//* successfull (status = 200), process the returned data. If the retrieval 
//* fails, solicit a parameter from user. 
//---------------------------------------------------------------------- 
{ 
  if (httpRequest.readyState == 4) 
  { 
	if(httpRequest.status == 200) 
	{ 
//--- get the parameter string sent by the servlet 
	  var textreturnarc = httpRequest.responseText;
	  var stringreturnarc = new String(textreturnarc);

	  if ((stringreturnarc.indexOf("html") >= 0) || 
	      (stringreturnarc.indexOf("error") >= 0))
	  {
	    alert ("Error retrieving parameter list - Issue with API or site error");
	    return;
	  }
	  storeoptionsarc(stringreturnarc,objsite,txtdb);
          //loadtxtpar();

//--- Store a cookie named after the specified site txtbox. The cookie has
//--- 3 parts: a comma-delimited parameter list, a reference copy of the 
//--- site in the txtbox, and the index of the selected parameter (0 at 
//--- this point)
  if (navigator.cookieEnabled) document.cookie = objsite.name + "=" + 
		escape(stringreturnarc + "/" + objsite.value + "/" + String(0));
	} 
	else 
	{ 
	  alert("Error loading page\n"+ httpRequest.status+":"+
		httpRequest.statusText); 
	} 
  } 
}
//======================================================================
function storeoptionsarc(parstring,site,txtdb) 
//* This function loads the specified select box from a passed 
//* comma-delimited string
//----------------------------------------------------------------------
{ 
  parstring = "," + parstring;
  var textarray = parstring.split(",");
  var plistarc = [];
  
  for (var indx = 1; indx < textarray.length; indx++){
    if (textarray[indx] != undefined){ //check if textarray exists, if not bail out
      if (indx == textarray.length-1){//textarray has a new line character that is loaded in from the API, purpose of if statement is to 
        //check if this is the last array entry and remove last character
        textarray[indx] = textarray[indx].substring(0,textarray[indx].length-1);//remove last character from textarray
        var parameter = window.hydromet_website_parameters[textarray[indx]];//read dictionary to match parameter to parameter description
        var parameter_description = String(textarray[indx]) + ' ' + parameter; //add parameter code to description
        plistarc.push(parameter_description);
        //objselpar[0].options[indx] = 
        //new Option(parameter_description,textarray[indx]); //send value and text label to select dropdown in HTML
      }
      else {//if not the last array entry do not remove last character
        var parameter = window.hydromet_website_parameters[textarray[indx]];//read dictionary to match parameter to parameter description
        var parameter_description = String(textarray[indx]) + ' ' + parameter;//add parameter code to description
        plistarc.push(parameter_description);
        //objselpar[0].options[indx] = 
        //new Option(parameter_description,textarray[indx]); //send value and text label to select dropdown in HTML
      }}};
      processparameterarc(plistarc,site);
  //objselpar[0].selectedIndex = parindex;  //-- set the selected index
}

//======================================================================
function loadselparday(objsite,txtdb)
//* Primary handler for loading a specified select box with a parameter
//* list based on the changed value of a specified site text box. 
//----------------------------------------------------------------------
{ 
    var url = "https://www.usbr.gov/gp-bin/daycsv.pl?" + objsite + ",+";
    if (objsite.value == "") return ;	//--- if site is blank, bail out
    var cookiename = objsite.name;		//-- the cookie name is the site txtbox name
    if (navigator.cookieEnabled) document.cookie = "parstring="; //-- clear
    if (window.XMLHttpRequest) 	//--- other browsers
    { 
    var httpRequest = new XMLHttpRequest(); 
    } 
    else
    { 
    var httpRequest = new ActiveXObject("Microsoft.XMLHTTP"); 
    } 
  
    httpRequest.open("GET", url, true); //-- invoke url and wait for return
    httpRequest.onreadystatechange = function() {processRequestday(objsite,txtdb,httpRequest); } ; 
    httpRequest.send(null); 
} 


//======================================================================
function processRequestday(objsite,txtdb,httpRequest) 
//* This is the call back method for the httpRequest state change event.
//* If the call is completed when the readyState is 4 and if the HTTP is 
//* successfull (status = 200), process the returned data. If the retrieval 
//* fails, solicit a parameter from user. 
//---------------------------------------------------------------------- 
{ 
  if (httpRequest.readyState == 4) 
  { 
	if(httpRequest.status == 200) 
	{ 
//--- get the parameter string sent by the servlet 
	  var textreturn = httpRequest.responseText;
    var stringreturn = new String(textreturn);

	  if ((stringreturn.indexOf("html") >= 0) || 
	      (stringreturn.indexOf("error") >= 0))
	  {
	    alert ("Error retrieving parameter list - Issue with API or site error");
	    return;
	  }

	  storeoptionsday(stringreturn,objsite,txtdb);
          //loadtxtpar();

//--- Store a cookie named after the specified site txtbox. The cookie has
//--- 3 parts: a comma-delimited parameter list, a reference copy of the 
//--- site in the txtbox, and the index of the selected parameter (0 at 
//--- this point)
	if (navigator.cookieEnabled) document.cookie = objsite.name + "=" + 
		escape(stringreturn + "/" + objsite.value + "/" + String(0));
	} 
	else 
	{ 
	  alert("Error loading page\n"+ httpRequest.status+":"+
		httpRequest.statusText); 
	} 
  } 
}
//======================================================================
function storeoptionsday(parstring,site,txtdb) 
//* This function loads the specified select box from a passed 
//* comma-delimited string
//----------------------------------------------------------------------
{ 
  parstring = "," + parstring;
  var textarray = parstring.split(",");
  var plistarc = [];
  var plistday = [];
  
    for (var indx = 1; indx < textarray.length; indx++){
    if (textarray[indx] != undefined){ //check if textarray exists, if not bail out
      if (indx == textarray.length-1){//textarray has a new line character that is loaded in from the API, purpose of if statement is to 
        //check if this is the last array entry and remove last character
        textarray[indx] = textarray[indx].substring(0,textarray[indx].length-1);//remove last character from textarray
        var parameter = window.hydromet_website_parameters[textarray[indx]];//read dictionary to match parameter to parameter description
        var parameter_description = String(textarray[indx]) + ' ' + parameter; //add parameter code to description
        plistday.push(parameter_description);
        //objselpar[0].options[indx] = 
        //new Option(parameter_description,textarray[indx]); //send value and text label to select dropdown in HTML
      }
      else {//if not the last array entry do not remove last character
        var parameter = window.hydromet_website_parameters[textarray[indx]];//read dictionary to match parameter to parameter description
        var parameter_description = String(textarray[indx]) + ' ' + parameter;//add parameter code to description
        plistday.push(parameter_description);
        //objselpar[0].options[indx] = 
        //new Option(parameter_description,textarray[indx]); //send value and text label to select dropdown in HTML
      }}};
    processparameterday(plistday,site);
  //objselpar[0].selectedIndex = parindex;  //-- set the selected index
}