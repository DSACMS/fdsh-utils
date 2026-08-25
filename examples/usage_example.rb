require_relative 'ruby-gateway'
require 'json'

def run_live_test
  puts "Starting live test for Hub::Gateway..."

  # Configuration from /tmp and provided URLs
  client_id = File.read('/tmp/oauth_client_id').strip rescue nil
  client_secret = File.read('/tmp/oauth_client_secret').strip rescue nil

  unless client_id && client_secret
    puts "Error: Could not read client credentials from /tmp/oauth_client_id or /tmp/oauth_client_secret"
    return
  end

  # URLs provided in issue update
  base_url = 'https://impl.hub.cms.gov:8443/'
  token_url = 'https://impl.hub.cms.gov:8443/auth/oauth/v2/token'
  education_path = 'mesh/imp1/NationalStudentClearinghouseService'

  gateway = Hub::Gateway.new(
    base_url: base_url,
    token_url: token_url,
    client_id: client_id,
    client_secret: client_secret,
    client_cert_path: '/tmp/oauth_client_id',
    client_key_path: '/tmp/oauth_client_secret',
    education_enrollment_url: education_path,
    resolve: "impl.hub.cms.gov:8443:127.0.0.1"
  )

  puts "Gateway initialized."

  puts "attempting to get access token..."
  gateway.send :access_token

  # Sample payload for Education Enrollment
  payload = {
    "personGivenName" => "Neil",
    "personSurName" => "Martinsen-Burrell",
    "asOfDate" => "1900-01-01",
    "termsAcceptedIndicator" => true,
    "personBirthDate" => "1999-01-01"
  }

  begin
    puts "Attempting to get education enrollment..."
    result = gateway.get_education_enrollment_v1(payload)
    puts "Success!"
    puts JSON.pretty_generate(result)
  rescue Hub::Gateway::ApiError => e
    puts "API Error: #{e.message}"
  rescue => e
    puts "Unexpected Error: #{e.class} - #{e.message}"
    puts e.backtrace.join("\n")
  end
end

run_live_test
