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

  this.topics = function(){
    return {
      success: function(callback){
        var t = [
          {
            content: 'Lorem ipsum dolor sit amet',
            weight: 0.5,
            keywords: [
              {
                content: 'Lorem ipsum',
                weight: 0.2
              },
              {
                content: 'Lorem ipsum',
                weight: 0.8
              },
              {
                content: 'Lorem ipsum',
                weight: 0.32
              },
              {
                content: 'Lorem ipsum',
                weight: 0.7
              },
              {
                content: 'Lorem ipsum',
                weight: 0.4
              },
              {
                content: 'Lorem ipsum',
                weight: 0.5
              },
              {
                content: 'Lorem ipsum',
                weight: 0.9
              },
              {
                content: 'Lorem ipsum',
                weight: 0.12
              },
              {
                content: 'Lorem ipsum',
                weight: 0.39
              },
              {
                content: 'Lorem ipsum',
                weight: 0.5
              }
            ]
          },
          {
            content: 'Dolor sit amet',
            weight: 0.5,
            keywords: [
              {
                content: 'Dolor sit',
                weight: 0.6
              },
              {
                content: 'Dolor sit',
                weight: 0.43
              },
              {
                content: 'Dolor sit',
                weight: 0.17
              },
              {
                content: 'Dolor sit',
                weight: 0.24
              },
              {
                content: 'Dolor sit',
                weight: 0.8
              },
              {
                content: 'Dolor sit',
                weight: 0.55
              },
              {
                content: 'Dolor sit',
                weight: 0.9
              },
              {
                content: 'Dolor sit',
                weight: 0.62
              },
              {
                content: 'Dolor sit',
                weight: 0.77
              },
              {
                content: 'Dolor sit',
                weight: 0.38
              }
            ]
          }
        ]

        callback(t);
      }
    }
  }
});
