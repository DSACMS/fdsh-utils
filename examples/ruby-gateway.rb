require 'net/http'
require 'json'
require 'uri'

module Hub
  # HubGateway abstracts the communication with the Hub Service API.
  # It handles authentication and provides a clean interface for domain services.
  class Gateway
    class ApiError < StandardError; end
    class AuthenticationError < ApiError; end

    attr_reader :base_url, :client_id, :client_secret, :token_url, :client_cert, :client_key, :resolve, :education_enrollment_url

    def initialize(base_url: ENV['HUB_API_URL'],
                   token_url: ENV['HUB_TOKEN_URL'],
                   client_id: ENV['HUB_CLIENT_ID'],
                   client_secret: ENV['HUB_CLIENT_SECRET'],
                   client_cert_path: ENV['HUB_CLIENT_CERT_PATH'],
                   client_key_path: ENV['HUB_CLIENT_KEY_PATH'],
                   resolve: ENV['HUB_RESOLVE'],
                   education_enrollment_url: ENV['HUB_EDUCATION_ENROLLMENT_URL'])
      @base_url = base_url
      @token_url = token_url
      @client_id = client_id
      @client_secret = client_secret
      @client_cert = load_cert(client_cert_path)
      @client_key = load_key(client_key_path)
      @resolve = parse_resolve(resolve)
      @education_enrollment_url = education_enrollment_url || '/api/v1/education-enrollments'
      @token = nil
    end

    # NSC V1 Education Enrollment Status
    # Returns the subject's current education enrollment status.
    #
    # Example payload:
    # {
    #   "nscRequest": {
    #     "personGivenName": "Neil",
    #     "personSurName": "Martinsen-Burrell",
    #     "asOfDate": "1900-01-01",
    #     "termsAcceptedIndicator": true,
    #     "personBirthDate": "1999-01-01"
    #   }
    # }
    def get_education_enrollment_v1(payload)
      post(education_enrollment_url, { nscRequest: payload })
    end

    private

    def post(path, body)
      uri = URI.join(base_url, path)
      request = Net::HTTP::Post.new(uri)
      request['Content-Type'] = 'application/json'
      request['Authorization'] = "Bearer #{access_token}"
      request.body = body.to_json

      execute(uri, request)
    end

    def execute(uri, request)
      hostname = uri.hostname
      port = uri.port

      if @resolve && @resolve[hostname] && @resolve[hostname][port]
        hostname = @resolve[hostname][port]
      end

      response = Net::HTTP.start(hostname, port,
                                 use_ssl: uri.scheme == 'https',
                                 cert: @client_cert,
                                 key: @client_key,
                                 ssl_version: :TLSv1_2,
                                 min_version: OpenSSL::SSL::TLS1_2_VERSION,
                                 max_version: OpenSSL::SSL::TLS1_2_VERSION) do |http|
        http.request(request)
      end

      handle_response(response)
    end

    def handle_response(response)
      case response.code.to_i
      when 200..299
        JSON.parse(response.body)
      when 401
        # Token might be expired, clear it and raise error
        @token = nil
        raise AuthenticationError, "Unauthorized: #{response.body}"
      else
        raise ApiError, "API request failed with status #{response.code}: #{response.body}"
      end
    end

    def access_token
      @token = fetch_token if @token.nil?
      @token
    end

    def fetch_token
      uri = URI(token_url)
      request = Net::HTTP::Post.new(uri)
      request.set_form_data(
        grant_type: 'client_credentials',
        client_id: client_id,
        client_secret: client_secret
      )

      hostname = uri.hostname
      port = uri.port
      connect_ip = @resolve[hostname][port]

      http = Net::HTTP.new(hostname, port, nil)
      http.ipaddr = connect_ip
      http.use_ssl = true
      http.cert = @client_cert
      http.key = @client_key
      http.min_version = OpenSSL::SSL::TLS1_2_VERSION
      http.max_version = OpenSSL::SSL::TLS1_2_VERSION

      response = http.start do
        http.request(request)
      end

      if response.code.to_i == 200
        JSON.parse(response.body)['access_token']
      else
        raise AuthenticationError, "Failed to obtain access token: #{response.body}"
      end
    end

    def load_cert(path)
      return nil unless path
      raise ApiError, "Certificate file not found at #{path}" unless File.exist?(path)
      OpenSSL::X509::Certificate.new(File.read(path))
    rescue OpenSSL::X509::CertificateError => e
      raise ApiError, "Failed to load certificate: #{e.message}"
    end

    def load_key(path)
      return nil unless path
      raise ApiError, "Key file not found at #{path}" unless File.exist?(path)
      OpenSSL::PKey.read(File.read(path))
    rescue OpenSSL::PKey::PKeyError => e
      raise ApiError, "Failed to load key: #{e.message}"
    end

    # Parses resolve string like "impl.hub.cms.gov:8443:127.0.0.1"
    def parse_resolve(resolve_str)
      return nil unless resolve_str
      host, port, ip = resolve_str.split(':')
      { host => { port.to_i => ip } }
    end
  end
end
