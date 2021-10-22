let apiExists = false;
let loopRunning = false;

function ajax_handler(action, message) {
    var post_message = {};
    post_message["action"] = action;
    post_message["message"] = message;
    $.ajax({
      url:'/hmi/ajax_req',
      type:"POST",
      data:JSON.stringify(post_message),
      contentType:"application/json; charset=utf-8",
      dataType:"json",
      success: function(response) {
        if (response["status"] === 200){
          if (action === "TDAmeritradeClient_new") {
              apiExists = true;
              button_visibility();
          } else if (action === "TDAmeritradeClient_delete") {
              apiExists = false;
              location.reload(true);
          } else if (action === "TDAmeritradeClient_startStreaming") {
              //pass
          } else if (action === "TDAmeritradeClient_stopStreaming") {
              //pass
          } else if (action == "info_refresh") {
              let l1quotes_info = response["response"]["l1quotes_info"];
              let ticker_info = response["response"]["ticker_info"];
              let api_info = response["response"]["api_info"];

              apiExists = api_info["apiExists"];
              loopRunning = api_info["loopRunning"];
              button_visibility();

              if (l1quotes_info) {
                  streamingdataInfo_handler(l1quotes_info);
              }
              if (ticker_info) {
                tickerRow_handler(ticker_info);
              }
          } else if (action == "tickerDetails") {
              let streams = response["response"]["streams"];
              modalTickerDetails_populate(message['row'], streams);
              $("#modalTickerDetails").modal("show");
          }
        }
      }
    })
}

function testMMI_ajax_handler(action, message) {
    var post_message = {};
    post_message["action"] = action;
    post_message["message"] = message;
    $.ajax({
      url:'/mmi',
      type:"POST",
      data:JSON.stringify(post_message),
      contentType:"application/json; charset=utf-8",
      dataType:"json",
      success: function(response) {
        if (response["status"] === 200){
          if (action === "fetch_tickerData") {
              //pass
          } 
        }
      }
    })
}

function htmlQuickscape(_tag, _class, _id, _innerHTML) {
    let _element = document.createElement(_tag);
    if ( _id !== null ) {
      _element.id = _id;
    }
    if ( _class !== null ) {
      _element.className = _class;
    }
    if ( _innerHTML !== null ) {
      _element.innerHTML = _innerHTML;
    }
    return _element;
}

function button_visibility() {
    if (apiExists == true) {
        $("button[id='TDAmeritradeClient_openModal']").attr('disabled', true);
        if (loopRunning == true) {
            $("button[id='TDAmeritradeClient_startStreaming']").attr('disabled', true);
            $("button[id='TDAmeritradeClient_stopStreaming']").attr('disabled', false);
            $("button[id='TDAmeritradeClient_delete']").attr('disabled', true);
        } else {
            $("button[id='TDAmeritradeClient_startStreaming']").attr('disabled', false);
            $("button[id='TDAmeritradeClient_stopStreaming']").attr('disabled', true);
            $("button[id='TDAmeritradeClient_delete']").attr('disabled', false);
        }
    } else {
        $("button[id='TDAmeritradeClient_openModal']").attr('disabled', false);
        $("button[id='TDAmeritradeClient_delete']").attr('disabled', true);
        $("button[id='TDAmeritradeClient_startStreaming']").attr('disabled', true);
        $("button[id='TDAmeritradeClient_stopStreaming']").attr('disabled', true);
    }
}

function streamingdataInfo_handler(l1quotes_info) {
    var oldestItem = l1quotes_info['oldestItem'];
    var currStreamStart = l1quotes_info['currStreamStart'];
    var daysStreaming = l1quotes_info['daysStreaming'];
    var lastUpdate = l1quotes_info['lastUpdate'];
    var updateFreq = l1quotes_info['updateFreq'];
    var nTickers = l1quotes_info['nTickers'];
    var nRowsAvg = l1quotes_info['nRowsAvg'];
    var nRowsMin = l1quotes_info['nRowsMin'];
    var nRowsMax = l1quotes_info['nRowsMax'];

    $("p[id='info_oldestItem']").text("Oldest Item: " + oldestItem);
    $("p[id='info_currStreamStart']").text("Current Stream Start: " + currStreamStart);
    $("p[id='info_lastUpdate']").text("Last Update: " + lastUpdate);
    $("p[id='info_updateFreq']").text("Update Frequency: " + updateFreq);
    $("p[id='info_nTickers']").text("n Tickers: " + nTickers);
    $("p[id='info_nRowsAvg']").text("n Rows (Avg): " + nRowsAvg);
    $("p[id='info_nRowsMin']").text("n Rows (Min): " + nRowsMin);
    $("p[id='info_nRowsMax']").text("n Rows (Max): " + nRowsMax);
}

function tickerRow_handler(ticker_info) {
    for (ticker in ticker_info) {
        var info = ticker_info[ticker]
        var row_id = 'tickerRow_' + ticker.replace(".", "_");
        let row = $("#"+row_id);
        if (row.length) {
            row.find("td[id='lastUpdate']").html(info['lastUpdate']);
            row.find("td[id='oldestItem']").html(info['oldestItem']);
            row.find("td[id='nRows']").html(info['nRows']);    
        } else {
            let newrow = create_tickerRow(ticker, info['lastUpdate'], info['oldestItem'], info['nRows']);
            let table_tbody = document.getElementById("tickerInfo_tbody");
            table_tbody.insertAdjacentElement('beforeend', newrow);
        } 
    }
}

function create_tickerRow(ticker_name, lastUpdate, oldestItem, nRows) {
    let row, ticker_col, lastUpdate_col, oldestItem_col, nRows_col;

    row = htmlQuickscape(
        'tr',
        null,
        "tickerRow_" + ticker_name.replace(".", "_"),
        null
    );
    ticker_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "ticker_name",
        ticker_name
    );
    lastUpdate_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "lastUpdate",
        lastUpdate
    );
    oldestItem_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "oldestItem",
        oldestItem
    );
    nRows_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "nRows",
        nRows
    );

    row.insertAdjacentElement('beforeend', ticker_col);
    row.insertAdjacentElement('beforeend', lastUpdate_col);
    row.insertAdjacentElement('beforeend', oldestItem_col);
    row.insertAdjacentElement('beforeend', nRows_col);
    return row
}

function create_streamRow(stream_id, timeStreaming, streamStart, streamEnd, streamValidation, nRows) {
    let row, streamID_col, timeStreaming_col, streamStart_col, streamEnd_col, streamValidation_col, nRows_col;

    row = htmlQuickscape(
        'tr',
        null,
        "streamRow_" + stream_id,
        null
    );
    streamID_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "streamID",
        stream_id
    );
    timeStreaming_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "timeStreaming",
        timeStreaming
    );
    streamEnd_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "streamEnd",
        streamEnd
    );
    streamStart_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "streamStart",
        streamStart
    );
    streamValidation_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "streamValidation",
        streamValidation
    );
    nRows_col = htmlQuickscape(
        'td',
        'pt-3-half',
        "nRows",
        nRows
    );

    row.insertAdjacentElement('beforeend', streamID_col);
    row.insertAdjacentElement('beforeend', timeStreaming_col);
    row.insertAdjacentElement('beforeend', streamEnd_col);
    row.insertAdjacentElement('beforeend', streamStart_col);
    row.insertAdjacentElement('beforeend', streamValidation_col);
    row.insertAdjacentElement('beforeend', nRows_col);
    return row
}

function customSearch(searchElement_id, tableElement_id) {
    search_input = document.getElementById(searchElement_id).value.toUpperCase();
    table = document.getElementById(tableElement_id);
    rows = table.getElementsByTagName("tr");
    for (i = 0; i < rows.length; i++) {
        ticker_field = rows[i].getElementsByTagName("td")[0];
        if (ticker_field) {
            ticker_value = ticker_field.textContent || ticker_field.innerText;
            if (ticker_value.toUpperCase().indexOf(search_input) > -1) {
                rows[i].style.display = "";
            } else {
                rows[i].style.display = "none";
            }
        }
    }
}

function modalTickerDetails_populate(row, streams) {
    let ticker_name = row.find("td[id='ticker_name']").text();
    let lastUpdate = row.find("td[id='lastUpdate']").text();
    let oldestItem = row.find("td[id='oldestItem']").text();
    let nRows = row.find("td[id='nRows']").text();  
    $("#streams_tbody").empty();

    Object.keys(streams).reverse().forEach(
        function(i) {
            let stream = streams[i];
            let nRows = stream['row count'];
            let start = stream['start'];
            let end = stream['end'];
            let validation = stream['validation'];
            let timeStreaming = stream['time streaming'];
            let newrow = create_streamRow(i, timeStreaming, start, end, validation, nRows);
            let table_tbody = document.getElementById("streams_tbody");
            table_tbody.insertAdjacentElement('beforeend', newrow);
          });;

    $("#modalTickerDetails_title").html("Details for " + ticker_name);
    $("#modalTickerDetails_streamingSince").html("N/A");
    $("#modalTickerDetails_lastUpdate").html(lastUpdate);
    $("#modalTickerDetails_oldestItem").html(oldestItem);
    $("#modalTickerDetails_nRows").html(nRows);
}

$(document).ready(function() {
    ajax_handler("info_refresh", NaN);
    setInterval(function () {ajax_handler("info_refresh", NaN);},5000);
});

$(document).on("click", "tr[id*='tickerRow_']", function(){
    let row = $(this);
    let ticker_name = row.find("td[id='ticker_name']").text();
    ajax_handler("tickerDetails", {'row': row, 'ticker': ticker_name});
});

$(document).on("click", "button[id='TDAmeritradeClient_submit']", function(){
    let TDAmeritradeClient_new={};
    TDAmeritradeClient_new["consumerkey"] = $("input[id='TDAmeritradeClient_consumerkey']").val();
    TDAmeritradeClient_new["redirecturi"] = $("input[id='TDAmeritradeClient_redirecturi']").val();
    TDAmeritradeClient_new["qoslevel"] = $("select[id='TDAmeritradeClient_qoslevel']").val();
    ajax_handler("TDAmeritradeClient_new", TDAmeritradeClient_new);
    $("#modalTDAmeritradeClient").modal("hide");
});

$(document).on("click", "button[id='TDAmeritradeClient_delete']", function(){
    ajax_handler("TDAmeritradeClient_delete", NaN);
});

$(document).on("click", "button[id='TDAmeritradeClient_startStreaming']", function(){
    ajax_handler("TDAmeritradeClient_startStreaming", NaN);
});

$(document).on("click", "button[id='TDAmeritradeClient_stopStreaming']", function(){
    ajax_handler("TDAmeritradeClient_stopStreaming", NaN);
});

$(document).on("click", "button[id='TestMMI_submit']", function(){
    let message={};
    message["ticker"] = $("input[id='TestMMI_ticker']").val();
    message["startDateTime"] = $("input[id='TestMMI_startDateTime']").val();
    message["endDateTime"] = $("input[id='TestMMI_endDateTime']").val();
    testMMI_ajax_handler("fetch_tickerData", message);
    $("#modalTestMMI").modal("hide");
});

