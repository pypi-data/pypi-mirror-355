schemarule = {
  "type": "object", 
  "properties": {
    "browser": {
      "type": "object",
      "properties": {
        "mode": {
          "type": "string", 
          "enum":["standard","headless","debug","login","proxy","remote"] 
        }, 
        "path": {
          "type": "string", 
          "enum":["config","env","manager"] 
        },
      },
      "required": ["mode","path"]
    },

    "basic": {
      "type": "object",
      "properties": {
        "mode": {
          "type": "string",
          "enum":["account","mac","qrc"] 
        }, 
        "login_url": {
          "type": "string",
          "format": "url",
           "not": { "pattern": "^$" },
        }, 
        "login_element": {
          "type": "string",
           "not": { "pattern": "^$" },
        },
        "login_max_time": {
          "type": "integer",
          "minimum":1,
          "maximum":20,
        },
        "login_max_retries":{
          "type": "integer",
          "minimum":1,
          "maximum":5,
        },
        "landing_url": {
          "type": "string",
          "format": "url",
          "not": { "pattern": "^$" },
        },
        "verify_max_time": {
          "type": "integer",
          "minimum":60,
          "maximum":600,
        },
      },
      "required": ["mode","login_url","login_element","login_max_time","landing_url","verify_max_time"]
    },
    
    "proxy":{
      "type": "object",
      "properties": {
        "scopes":{
          "type":"array"
        },
      },
      "required": ["scopes"]
    },

    "cookie":{
      "type": "object",
      "properties": {
        "url_pattern":{
          "type": "string",
          "format": "regex"
        },        
        "value_pattern":{
          "type": "string",
          "format": "regex"
        },        
      },
      "required": ["url_pattern","value_pattern"]
    },
    
    "preparation":{
      "type": ["object","null"],
    },

    "execution":{
      "type": "object",
    },

    "cleanup":{
      "type": ["object","null"],
    },

  },

  "required": ["browser","basic","proxy","cookie","preparation","execution","cleanup"],
}
