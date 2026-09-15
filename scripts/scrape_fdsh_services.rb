require 'net/http'
require 'uri'
require 'nokogiri'
require 'json'

COOKIES = ENV['COOKIE_VALS']

# Scraper for FDSH services from CMS zONE
class FDSHScraper
  BASE_URL = 'https://zone.cms.gov'

  # Headers and Cookies from the provided curl reference
  HEADERS = {
    'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language' => 'en-US,en;q=0.9',
    'User-Agent' => 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36',
    'Referer' => 'https://zone.cms.gov/community/cms-fdsh-services-repository'
  }

  def self.fetch_all_pages(base_url, total_pages = 6, fetch_attachments = false)
    all_services = []
    (0...total_pages).each do |page|
      separator = base_url.include?('?') ? '&' : '?'
      page_url = "#{base_url}#{separator}page=#{page}"
      $stderr.puts "Fetching page #{page}..."
      page_services = fetch_services(page_url, fetch_attachments)

      # Stop if we get no results on a page (might be fewer pages than expected)
      break if page_services.empty? && page > 0

      all_services.concat(page_services)
    end
    # De-duplicate based on link just in case
    all_services.uniq { |s| s[:link] }
  end

  def self.fetch_services(page_url, fetch_attachments = false)
    html = get_url(page_url)
    return [] unless html

    services = parse_services(html)

    if fetch_attachments
      services.each_with_index do |service, index|
        $stderr.puts "Fetching attachments for [#{index + 1}/#{services.size}]: #{service[:title]}..."
        service[:attachments] = fetch_attachments_for_service(service[:link])
      end
    end

    services
  end

  def self.get_url(url)
    uri = URI.parse(url)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = (uri.scheme == 'https')

    request = Net::HTTP::Get.new(uri)
    HEADERS.each { |k, v| request[k] = v }
    request['Cookie'] = COOKIES

    begin
      response = http.request(request)
    rescue => e
      $stderr.puts "Error: Failed to connect to #{url} - #{e.message}"
      return nil
    end

    if response.code == '200'
      response.body
    else
      $stderr.puts "Error: Received HTTP #{response.code} for #{url}"
      nil
    end
  end

  def self.parse_services(html)
    doc = Nokogiri::HTML(html)
    services = []

    # Strategy 1: Look for Drupal View rows which are common for listing items
    doc.css('div.views-row, td.views-field-title').each do |row|
      link_element = row.at_css('a')
      next unless link_element

      title = link_element.text.strip
      href = link_element['href']
      next if title.empty? || !href

      full_link = href.start_with?('http') ? href : "#{BASE_URL}#{href}"
      services << { title: title, link: full_link }
    end

    # Strategy 2: If nothing found, look for any links in the main content area
    if services.empty?
      # Try to narrow down to main content if possible
      content = doc.at_css('#main-content, .region-content, .view-content') || doc
      content.css('a').each do |a|
        href = a['href'] || ''
        # Filter for likely service links
        if href.include?('/group/') || href.include?('/service/') || href.include?('/node/')
          title = a.text.strip
          next if title.empty? || title.length > 150

          full_link = href.start_with?('http') ? href : "#{BASE_URL}#{href}"
          # Avoid duplicates and common UI links
          next if services.any? { |s| s[:link] == full_link }
          next if ['Read more', 'View', 'Edit'].include?(title)

          services << { title: title, link: full_link }
        end
      end
    end

    services
  end

  def self.fetch_attachments_for_service(service_url)
    html = get_url(service_url)
    return [] unless html

    doc = Nokogiri::HTML(html)
    attachments = []

    # Common Drupal patterns for attachments
    selectors = [
      '.field-name-field-attachments a',
      '.attachments a',
      '.file a',
      'a[href*="/sites/default/files/"]',
      '.field-type-file a'
    ]

    doc.css(selectors.join(', ')).each do |a|
      href = a['href']
      next unless href

      # Filter for actual file links, avoiding common false positives
      next if href.include?('/edit') || href.include?('/delete')

      # We want to keep links to documents/files
      name = a.text.strip
      name = File.basename(href) if name.empty?

      full_link = href.start_with?('http') ? href : "#{BASE_URL}#{href}"

      next if attachments.any? { |att| att[:link] == full_link }

      attachments << { name: name, link: full_link }
    end

    attachments
  end
end

# CLI Logic
if __FILE__ == $0
  if ARGV.include?('--help') || ARGV.include?('-h')
    puts "Usage: ruby scrape_fdsh_services.rb [PAGE_URL] [--all] [--no-attachments]"
    puts "Options:"
    puts "  PAGE_URL        Specific URL to fetch (default: https://zone.cms.gov/group/1981/services)"
    puts "  --all           Fetch all pages (0-5). This is the default if no URL is provided."
    puts "  --no-attachments Skip fetching attachments for each service."
    puts "Outputs JSON to stdout. Progress/errors to stderr."
    exit
  end

  # Filter out flags from arguments to find the target URL
  flags = ['--all', '--no-attachments']
  remaining_args = ARGV.reject { |arg| flags.include?(arg) }

  target_url = remaining_args[0] || 'https://zone.cms.gov/group/1981/services'
  fetch_attachments = !ARGV.include?('--no-attachments')

  if ARGV.include?('--all') || remaining_args[0].nil?
    $stderr.puts "Fetching all services (pagination 0-5) from: #{target_url}..."
    services = FDSHScraper.fetch_all_pages(target_url, 6, fetch_attachments)
  else
    $stderr.puts "Fetching services from: #{target_url}..."
    services = FDSHScraper.fetch_services(target_url, fetch_attachments)
  end

  if services.any?
    puts JSON.pretty_generate(services)
  else
    $stderr.puts "No services found."
    $stderr.puts "Note: The session cookies in the script might have expired."
    puts [].to_json
  end
end
