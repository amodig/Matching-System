var MatchingApp = angular.module('MatchingApp', ['ngRoute', 'ngSanitize', 'ui.gravatar', 'btford.markdown']);

MatchingApp.config(function($routeProvider){
  $routeProvider
    .when('/profile', {
      controller: 'ProfileController',
      templateUrl: 'static/app/views/profile.html'
    })
    .when('/engine', {
      controller: 'IterationController',
      templateUrl: 'static/app/views/engine.html'
    })
    .otherwise({
      redirectTo: '/profile'
    });
});

MatchingApp.config(function($interpolateProvider){
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
});
