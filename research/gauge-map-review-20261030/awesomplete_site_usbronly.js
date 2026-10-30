//Build an automated site list through Hydromet APIs
document.addEventListener("DOMContentLoaded", function() {
    //Define where the site list should be stored
    var input = document.getElementById("site_list");

    //Build the API request from site.csv, this is an API with all active (updated at 6 AM each morning) Hydromet sites in a CSV format
    var ajax = new XMLHttpRequest();
    ajax.open("GET", "https://www.usbr.gov/gp/hydromet/site.csv", true);
    ajax.onload = function() {
        //Once the API content loads, send the response to function CSVtoArray
        var Text = ajax.responseText;
        var list = CSVtoArray(Text);

        //After completing CSVtoArray, send function response to the HTML element 
        new Awesomplete(input,{ list: list }); 
    };
    ajax.send();

    function CSVtoArray(text) {
        var array = text.split("\n"); //Split API response on each new line
        headers = array[0].split(","); // Split the header row on each comma, store the header names in an array
        var j = headers.indexOf("SITE"); // Find the column titled "SITE" and store the index value, repeat on additional lines
        var k = headers.indexOf(" GRP");
        var l = headers.indexOf(" DESCR");
        var m = headers.indexOf("ACL");
        var n = headers.indexOf(" STATYPE");
        b = [];
        
        for (var i = 1; i < array.length; i++) { //Begin for loop for remaining rows to pull site metadata
            text = array[i]; //Pull in each data row
            c = parseLines(text); //Send each data row to the parseLines function
            b.push(c);

            function parseLines(text) {
                // Return array of string values, or NULL if CSV string not well formed. This is to deal with , " ' and other characters that mess up generic csv formats
                //re_valid and re_value are regex statements defined at bottom of script
                var re_valid = /^\s*(?:'[^'\\]*(?:\\[\S\s][^'\\]*)*'|"[^"\\]*(?:\\[\S\s][^"\\]*)*"|[^,'"\s\\]*(?:\s+[^,'"\s\\]+)*)\s*(?:,\s*(?:'[^'\\]*(?:\\[\S\s][^'\\]*)*'|"[^"\\]*(?:\\[\S\s][^"\\]*)*"|[^,'"\s\\]*(?:\s+[^,'"\s\\]+)*)\s*)*$/;
                var re_value = /(?!\s*$)\s*(?:'([^'\\]*(?:\\[\S\s][^'\\]*)*)'|"([^"\\]*(?:\\[\S\s][^"\\]*)*)"|([^,'"\s\\]*(?:\s+[^,'"\s\\]+)*))\s*(?:,|$)/g;
               
                if (!re_valid.test(text)) return null; // Return NULL if input string is not well formed CSV string. 

                var a = []; // Initialize array to receive values.
                text.replace(re_value, // Iterate through each character in the string to check for additional characters that could impact CSV parsing
                    function(m0, m1, m2, m3) {
                    // Remove backslash from \' in single quoted values.
                    if      (m1 !== undefined) a.push(m1.replace(/\\'/g, "'"));
                    // Remove backslash from \" in double quoted values.
                    else if (m2 !== undefined) a.push(m2.replace(/\\"/g, '"'));
                    else if (m3 !== undefined) a.push(m3);
                    return ''; // Return empty string.
                });
                // Handle special case of empty last value.
                if (/,\s*$/.test(text)) a.push('');
                return a; // Push an array with each row's CSV value entries after they have been formatted for parsing
            };
        };
        
        let e = [];
        //Use the b array that houses each row's CSV data to process and store list data needed for the dropdowns
        for (var o = 0; o < b.length; o++) { // Iterate through each CSV row
            item = b[o];
            siteID = item[j]; //Use the header indexes to asign items to site properties
            siteGroup = item[k];
            siteName = item[l];
            siteArea = item[m];
            siteType = item[n];

            //If the site belongs to USBR OR if the site is an OTAO Reservoir, then continue to process the data in each row
            if (siteGroup == "10" || siteGroup == "11" || siteGroup == "0" || (siteArea == "OTAO" && siteType == "RES")) { 
                //The following sites are all exceptions, they belong to USBR but are managed through USGS so we should not display them in the data dropdowns
                if (siteID !== "BABM" && siteID !== "BCHM" && siteID !== "BDCM" && siteID !== "BFCE" && siteID !== "BFWY" && siteID !== "CRED" && siteID !== "SFKSM"
                && siteID !== "ESTSPKCO" && siteID !== "MARM" && siteID !== "MREC" && siteID !== "NFMA" && siteID !== "SRBM" && siteID !== "TMRM") {
                    //Generate the list format
                    let d = [siteID + " - " + siteName, siteID];
                    e.push(d);  
                }
            // HEBR and BCLM are not owned by USBR, but they are managed in conjunction with USBR and external agencies and should be displayed in data dropdowns
            } else if (siteID == "HEBR" || siteID == "BCLM") {
                //Generate the list format
                let d = [siteID + " - " + siteName, siteID];
                e.push(d);  
            }
        }
        //Send the array of sites and descriptions to the function call
        return e;
    };
});


/* Comments for REGEX from https://stackoverflow.com/questions/8493195/how-can-i-parse-a-csv-string-with-javascript-which-contains-comma-in-data
re_value = r"""
# Match one value in valid CSV string.
(?!\s*$)                            # Don't match empty last value.
\s*                                 # Strip whitespace before value.
(?:                                 # Group for value alternatives.
  '([^'\\]*(?:\\[\S\s][^'\\]*)*)'   # Either $1: Single quoted string,
| "([^"\\]*(?:\\[\S\s][^"\\]*)*)"   # or $2: Double quoted string,
| ([^,'"\s\\]*(?:\s+[^,'"\s\\]+)*)  # or $3: Non-comma, non-quote stuff.
)                                   # End group of value alternatives.
\s*                                 # Strip whitespace after value.
(?:,|$)                             # Field ends on comma or EOS.
"""
re_valid = r"""
# Validate a CSV string having single, double or un-quoted values.
^                                   # Anchor to start of string.
\s*                                 # Allow whitespace before value.
(?:                                 # Group for value alternatives.
  '[^'\\]*(?:\\[\S\s][^'\\]*)*'     # Either Single quoted string,
| "[^"\\]*(?:\\[\S\s][^"\\]*)*"     # or Double quoted string,
| [^,'"\s\\]*(?:\s+[^,'"\s\\]+)*    # or Non-comma, non-quote stuff.
)                                   # End group of value alternatives.
\s*                                 # Allow whitespace after value.
(?:                                 # Zero or more additional values
  ,                                 # Values separated by a comma.
  \s*                               # Allow whitespace before value.
  (?:                               # Group for value alternatives.
    '[^'\\]*(?:\\[\S\s][^'\\]*)*'   # Either Single quoted string,
  | "[^"\\]*(?:\\[\S\s][^"\\]*)*"   # or Double quoted string,
  | [^,'"\s\\]*(?:\s+[^,'"\s\\]+)*  # or Non-comma, non-quote stuff.
  )                                 # End group of value alternatives.
  \s*                               # Allow whitespace after value.
)*                                  # Zero or more additional values
$                                   # Anchor to end of string.
"""*/