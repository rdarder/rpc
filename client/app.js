(function () {
  var app = angular.module('app', ['rpc']);
  app.run([
    '$location', '$rootScope', 'rpc', 'rpc_watch',
    function (location, rootScope, rpc, rpc_watch) {
      var ws = new WebSocket(
        'ws://' + location.host() + ':' + location.port() + '/rpc'
      );
      rootScope.rpc = rpc.connect(ws);
      rootScope.rpc_watch = rpc_watch('rpc');
    }
  ]);

  app.controller('errors', [
    '$scope', function (self) {
      self.show_errors = false;
      self.new_errors = [];
      self.$on('rpc', function (event, err, call) {
        var full_err = {
          server: err,
          client: {
            service: call.service,
            method:  call.method,
            args:    call.args
          }};
        console.log(full_err);
        self.new_errors.splice(0, 0, full_err);
        self.select(self.new_errors.length - 1);
      });
      self.clear = function () {
        self.new_errors = [];
      };
      self.select = function (index) {
        self.current_error = self.new_errors[index];
      }
    }
  ]);
  app.filter('args', function () {
    return  function (values, sep) {
      formatted = [];
      if (!sep) {
        sep = ',';
      }
      angular.forEach(values, function (value) {
        formatted.push(angular.toJson(value));
      });
      return formatted.join(sep);
    }
  });


  app.controller('main', [
    '$scope', function (self) {
      self.a = 10;
      self.b = 15;
      self.rpc_watch('math.fast_add', 'a', 'b').into('result');

      self.rpc('db.list_tables').then(function (tables) {
        self.table_list = tables
      });
      self.rpc_watch('db.get_create', 'table').into('table_create');
      self.rpc_watch('db.get_all_rows', '; false').into('table_data');
    }
  ]);

}());
