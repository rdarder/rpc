(function () {
  var app = angular.module('app', ['rpc', 'bootstrap']);
  app.run([ '$location', '$rootScope', 'rpc', 'rpc_watch',
    function (location, rootScope, rpc, rpc_watch) {
      rootScope.rpc = rpc.init('/rpc');
      rootScope.rpc_watch = rpc_watch('rpc');
    }
  ]);

  app.controller('main', [
    '$scope', function (self) {
      self.a = 15;
      self.b = 1;
      self.div_style = 'fast';

      self.server_division = function () {
        self.rpc('math.div', self.a, self.b).then(function (result) {
          self.result = result;
        });
      };
      self.$watch('a', self.server_division);
      self.$watch('b', self.server_division);
      self.$watch('div_style', self.server_division);


      self.rpc('db.list_tables').then(function (tables) {
        self.table_list = tables
      });
      self.rpc_watch('db.get_create', 'table').into('table_create');
      self.rpc_watch('db.get_all_rows', 'table').into('table_data');
    }
  ]);

}());
