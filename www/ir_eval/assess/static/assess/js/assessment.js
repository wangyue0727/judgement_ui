function is_handheld(){
  //return (navigator.userAgent.indexOf("iPad") != -1);
  return /Android|iPhone|iPad|IEMobile|Mobile/i.test(navigator.userAgent);
}

function is_phone(){
  //return (navigator.userAgent.indexOf("iPhone") != -1);
  return $(window).width() <= 768;

}

$(document).ready(function(){
  // set up the header, iframe and footer
  $('div#container').removeClass( "container" ).addClass( "container-fluid" );
  //$('div#container').height($(window).height());
  $('div#raw_html_viewer').height($(window).height()-55);
  $('body').css('padding-bottom', '0px');
  $('div#footer').remove();

  $( window ).resize(function() {
    $('div#raw_html_viewer').height($(window).height()-55);
  });
 
  $('div#float-info-wrapper').click(function(){
    $(this).clearQueue().slideUp('fast');
  });

  // initialize_inputs(); // Uncomment this when Aspect is used in judgement
  
  $( "input" ).on( "click", function() {
    //**************************************************
    // Uncomment this when Aspect is used in judgement
    //**************************************************
    // if (this.id.match("rel-no$") && $(this).is(":checked")){
    //   var sentence_id=this.id.split('-')[0];    
    //   $('#'+sentence_id+'-aspect-selection').hide();
    //   $('#other-keywords-'+sentence_id).val("");
    //   $('#other-keywords-'+sentence_id).hide();
    // } else if (this.id.match("rel-yes$") && $(this).is(":checked")){
    //   var sentence_id=this.id.split('-')[0];    
    //   $('#other-keywords-'+sentence_id).val("");
    //   $('#'+sentence_id+'-aspect-selection').show();
    // }
    if(validation()){
      $('button#label-submit').prop('disabled', false);
    } else {
      $('button#label-submit').prop('disabled', 'disabled');
    }
  });

    //**************************************************
    // Uncomment this when Aspect is used in judgement
    //**************************************************

  // $( "select" ).on( "click", function() {
  //   if (this.id.match("-aspect-selection$")) {      
  //     var sentence_id=this.id.split('-')[0]; 
  //     $( "#"+sentence_id+"-aspect-selection option:selected" ).each(function() {
  //       if ($( this ).val() === "other") {
  //         $('#other-keywords-'+sentence_id).val("");
  //         $('#other-keywords-'+sentence_id).show();
  //       } else {
  //         $('#other-keywords-'+sentence_id).val("");
  //         $('#other-keywords-'+sentence_id).hide();
  //       }
  //     });    
  //   }
  //   if(validation()){
  //     $('button#label-submit').prop('disabled', false);
  //   } else {
  //     $('button#label-submit').prop('disabled', 'disabled');
  //   }
  // });

  // set up the label form
  $('form#label').submit(function(event){
    event.preventDefault();
    
    // first, perform form validation
    var aspect_error=0;
    var keyword_error=0;
    var sentence_level_bug=0;
    var consistent_error=0;
    if ($("input[name='t-relevance']:checked").val() == "yes"){

    //**************************************************
    // Uncomment this when Aspect is used in judgement
    //**************************************************

      // $("select[id='t-aspect-selection'] option:selected").each(function() {
      //   if ($( this ).val() == 'undefined'){
      //     aspect_error=1;
      //   } else if ($( this ).val() == 'other'){
      //     var regex = /^\s+$/;
      //     if (!$("input[id=other-keywords-t]").val().trim()){
      //       keyword_error=1;
      //     }
      //   }
      // });
      sentence_level_bug=1;
    }

    var total = $("input[name$='relevance']").length;
    total = total / 2;
    total = total - 2;
    for (var i = 0; i < total; i++) {
      if ($("input[name='"+i+"-relevance']:checked").val() == "yes") { 

    //**************************************************
    // Uncomment this when Aspect is used in judgement
    //**************************************************

        // $("select[id='"+ i +"-aspect-selection'] option:selected").each(function() {
        //   if ($( this ).val() == 'undefined'){
        //     aspect_error=1;
        //   } else if ($( this ).val() == 'other'){
        //     var regex = /^\s+$/;
        //     if (!$("input[id='other-keywords-"+i+"']").val().trim()) {
        //       keyword_error=1;
        //     }
        //   }
        // }); 
        sentence_level_bug=1;
      }   
    } 

    if ($("input[name='overall-relevance']:checked").val() == "no" && sentence_level_bug == 1){
      consistent_error=1;
    } else if ($("input[name='overall-relevance']:checked").val() == "yes" && sentence_level_bug == 0){
      consistent_error=1;
    }
    
    if (consistent_error){
      $('p#submit-info').hide();
      $('p#submit-success').hide();
      msg = 'The judgement on sentence level is not consistent with the one on review level.  (Click to dismiss)';
      $('p#submit-error').text(msg).show();
      $('div#float-info-wrapper').slideDown('fast', function(){
        $(this).delay(6000).slideUp('fast');
      });     
    } 
    //**************************************************
    // Uncomment this when Aspect is used in judgement
    //**************************************************

    // else if (keyword_error){
    //   $('p#submit-info').hide();
    //   $('p#submit-success').hide();
    //   msg = 'Please provide detailed keywords for the aspect(s) not in list.  (Click to dismiss)';
    //   $('p#submit-error').text(msg).show();
    //   $('div#float-info-wrapper').slideDown('fast', function(){
    //     $(this).delay(6000).slideUp('fast');
    //   });          
    // } else if (aspect_error){      
    //   $('p#submit-info').hide();
    //   $('p#submit-success').hide();
    //   msg = 'Please select aspect for the bug report sentence(s).  (Click to dismiss)';
    //   $('p#submit-error').text(msg).show();
    //   $('div#float-info-wrapper').slideDown('fast', function(){
    //     $(this).delay(6000).slideUp('fast');
    //   });          
    // }
    else{
      // we are ready to submit
      $('p#submit-success').hide();
      $('p#submit-error').hide();
      $('p#submit-info').text('Submitting ...').show();
      
      $('div#float-info-wrapper').slideDown('fast', function(){
        // animation complete
        $(this).delay(1000).slideUp('fast');
      
        url_path = $('form#label').attr('action');
        $.post(url_path, $('form#label').serialize())
        .done(function(response){
          $('p#submit-info').hide();
          $('p#submit-error').hide();
          msg = response.info + ' Will return.';
          $('p#submit-success').text(msg).show();
          // return to the query page
          setTimeout(function(){
            window.location.href = response.redirect;
          }, 1000);
        })
        .fail(function(response) {
          $('p#submit-info').hide();
          $('p#submit-success').hide();
          msg = 'Oops. An error has occurred: ' 
            + response.responseJSON.error_msg + ' (Click to dismiss)';
          //msg = 'Oops. An error has occurred. (Click to dismiss)';
          $('p#submit-error').text(msg).show();
          $('div#float-info-wrapper').delay(5000).slideUp('fast');
        })
        .always(function() {
          // do something always
        });
      });
    }
  });
  
  $('button#label-submit').prop('disabled', 'disabled');

  $('a#view_itunes').click(function(event){
    event.preventDefault();
    url = $(this).attr('url');
    console.log('Redirect to ' + url);
    $('#doc_view').attr('src', url);
    $('li.active').removeClass();
    $(this).parent().addClass('active');
  });
  
  $('a#view_raw_doc').click(function(event){
    event.preventDefault();
    url = $(this).attr('url');
    console.log('Redirect to ' + url);
    $('#doc_view').attr('src', url);
    $('li.active').removeClass();
    $(this).parent().addClass('active');
  });
});

function initialize_inputs(){
  var total = $("input[name$='relevance']").length;
  total = total / 2;
  total = total - 2;
  if ($("input[name='t-relevance']:checked").val() == "yes") {
    // alert($("input[name='t-relevance']:checked").val());
    $("[id='t-aspect-selection']").show();
    if ($("[id='t-aspect-selection']").val() == "other"){
      $("[id='other-keywords-t']").show();    
    } else {
      $("[id='other-keywords-t']").hide();    
    }    
  } else {
    $("[id='t-aspect-selection']").hide();
    $("[id='other-keywords-t']").hide();    
  }
  for (var i = 0; i < total; i++) {
    if ($("input[name='"+i+"-relevance']:checked").val()=="yes") { 
      $("[id='"+i+"-aspect-selection']").show();
      if ($("[id='"+i+"-aspect-selection']").val() == "other"){
        $("[id='other-keywords-"+i+"']").show(); 
      } else {
        $("[id='other-keywords-"+i+"']").hide(); 
      }    
    } else {
      $("[id='"+i+"-aspect-selection']").hide();
      $("[id='other-keywords-"+i+"']").hide(); 
    }   
  };
}

function validation(){
  var total = $("input[name$='relevance']").length;
  total = total / 2;
  total = total - 2;
  if (!$("input[name='t-relevance']:checked").val()) { 
    return false; 
  } else if (!$("input[name='overall-relevance']:checked").val()) { 
    return false; 
  } else {
    for (var i = 0; i < total; i++) {
      if (!$("input[name='"+i+"-relevance']:checked").val()) { 
        return false; 
      }     
    };
  }
  return true;
}