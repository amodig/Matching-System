
function tableCreate(){

    var _fetch_charts = function(callback){
	
        $.get("/tables_data", function(data){
            	console.log(data);
            	data = data.tables;
	    	persons = data[0].persons
		words = data[0].words
	    console.log(persons);
	    console.log(words);
		callback(persons,words);
        })
    }

    _fetch_charts(function(persons,words){
		var body = document.getElementsByTagName("body")[0];
      // create elements <table> and a <tbody>
		var tbl     = document.createElement("table");
		tbl.setAttribute("class", "sortable");
		var tblHead = document.createElement("thead");
      var tblBody = document.createElement("tbody");

	// headers creation
	var row = document.createElement("tr");
	var cell = document.createElement("th");
	var cellText = document.createTextNode("Person");
	cell.appendChild(cellText);
	row.appendChild(cell);
	for (var i = 0; i < 2; i++)
	{
		var cell = document.createElement("th");  
		var cellText = document.createTextNode("word"); 
		cell.appendChild(cellText);
		row.appendChild(cell);
	}

        //row added to end of table head
	tblHead.appendChild(row);
        // append the <tbody> inside the <table>
   tbl.appendChild(tblHead);

        // cells creation
        for (var j = 0; j < persons.length; j++) {
            // table row creation
            var row = document.createElement("tr");
            var cell = document.createElement("td");
				var cellText = document.createTextNode(persons[j]);
            cell.appendChild(cellText);
            row.appendChild(cell);
            
            // sort words[j] array
            word_ids = words[j].sort(function(a, b){return a-b});
            k = 0;
            for (var i = 0; i < 2; i++) {
                // create element <td> and text node 
                //Make text node the contents of <td> element
                // put <td> at end of the table row
					var cell = document.createElement("td");
					if (i == word_ids[k]) {
						var cellText = document.createTextNode("0"); 
						k++;
					}
					else {
						var cellText = document.createTextNode("0"); 
					}
               cell.appendChild(cellText);
               row.appendChild(cell);
            }

            //row added to end of table body
            tblBody.appendChild(row);
        }

        // append the <tbody> inside the <table>
        tbl.appendChild(tblBody);
         // tbl border attribute to 
        tbl.setAttribute("border", "2");
        // put <table> in the <body>
        body.appendChild(tbl);


	})
}
tableCreate();

