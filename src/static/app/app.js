var MatchingApp = angular.module('MatchingApp', []);

MatchingApp.config(function($interpolateProvider){
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
});
