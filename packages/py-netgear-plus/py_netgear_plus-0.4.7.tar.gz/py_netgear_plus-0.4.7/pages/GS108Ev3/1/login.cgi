<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<link rel="stylesheet" type="text/css" href="login.css?v3.e">
<title>NETGEAR GS108Ev3</title>
<script src="login.js?v3.e" type="text/javascript"></script>
<script src="jquery.md5.js" type="text/javascript"></script>
<script language="JavaScript">
function submitLogin()
{
    encryptPwd();
	document.forms[0].submit();
	return true;
}
function showErrmsg()
{
	var errMsg = document.getElementById("err_msg");
	var errDiv = document.getElementById("pwdErr");

	if (errMsg.value != "")
	{
		errDiv.innerHTML = errMsg.value;
	}
	else
	{
		errDiv.innerHTML = "";
	}
}
</script>
</head>
<body onload="init();showErrmsg();changeLoginButtonStyle();">
<div id="mainArea" class="mainArea">
  <div id="mainTitleArea" class="mainTitleArea">
   <img class="customGraph" src="NgrLogo.png">
   <img class="factGraph" src="ContentVisual.png">
   <div class="switchInfo">GS108Ev3 - 8-Port Gigabit Ethernet Smart Managed Plus Switch</div>
  </div>
  <div id="loginContainer" class="loginContainer">
   <form method="post" action="login.cgi" name="login" autocomplete="off" onSubmit="return false;" >
    <input type="hidden" id="submitPwd" name="password" value="">
    <div id="contentArea">
	 <div id="loginArea" class="loginArea">
	  <div id="loginTitleArea">
	   <table>
		<tr>
		<script>tbhdrLoginTable('Anmeldung');</script>
		</tr>
		<tr>
		 <td></td>
		 <td colspan="2">
		  <table>
		   <tr>
		    <td class="topLoginTitleBottomBar"></td>
		   </tr>
		  </table>
		 </td>
		 <td></td>
		</tr>
	   </table>
	  </div>
	  <div id="loginBlkbArea" class="bClass">
	   <div id="loginDiv" class="loginBox">
	    <div id="loginTDataArea" class="tableData mTop25">
	     <table id="loginTData">
	      <tbody>
	       <tr>
		  <td width="23px"><div></div></td>
		  <td width="100px">
		   <div class="colInterval textLeft">Passwort</div>
		  </td>
		  <td width="290px">
		   <input id="password" class="textInputStyle textInputLength" type="password"  onkeypress="onEnterSub(event);" maxlength="20" style="border:1px #CCCCCC solid;">
		  </td>
		  <td width="23px"><div></div></td>
              </tr>
              <tr>
		  <td width="23px"><div></div></td>
		  <td width="100px"><div></div></td>
		  <td width="290px">
		   <div id="pwdErr" class="pwdErrStyle"></div>
		  </td>
		  <td width="23px"><div></div></td>
		</tr>
 			 <tr>
 			  <td width="23px"><div></div></td>
 			  <td width="100px"><div></div></td>
 			  <td width="290px">
				<a id="loginBtn" class="loginBtnStyle" href="javascript:submitLogin()">Anmeldung</a>
 			  </td>
 			  <td width="23px"><div></div></td>
 			 </tr>
 			</tbody>
 		   </table>
 		  </div></div></div></div></div>
		  <input type=hidden id="rand" name="rand" value='1763184457' disabled>
 		  <input type=hidden name='err_msg' id='err_msg' value='Das Passwort ist ungültig.' disabled>
 		 </form>
 		</div>
         <div class="footerImg">
          <div class="copyrightGraphWrap">
           <span>&copy; NETGEAR, Inc. Alle Rechte vorbehalten.</span>
          </div>
          <img style="float:right;" src="Footer_Facet.png">
         </div>
  </div>
</body>
</html>
