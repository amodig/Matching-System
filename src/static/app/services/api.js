MatchingApp.service('Api', function($http){
  this.updateBio = function(newBio){
    return $http.post('/update_bio', { bio_new_text: newBio });
  }

  this.getProfile = function(){
    return $http.get('/profile');
  }

  this.updateArticle = function(article){
    $http.post('/article/' + article.key + '/edit', { new_title: article.title, new_abstract: article.abstract });
  }

  this.getArticleWithKey = function(key){
    return $http.get('/article/' + key);
  }

  this.next = function(feedback){
    return $http.post('/feedback', feedback);
  }

  this.getTopicRelatedArticles = function(topicId){
    return $http.get('/topic/' + topicId + '/articles');
  }

  this.topics = function(options){


    return $http.get('/topicsearch/' + options.keyword.replace(/ /g, '').toLowerCase());
  }
});
