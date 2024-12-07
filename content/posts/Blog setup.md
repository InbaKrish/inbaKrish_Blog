---
tags:
  - InbaKrishBlog
date: 2024-12-07
draft: "false"
title: Blog Setup
---


Have you ever wondered how to build an image search engine (like Google Images, Myntra fashion products search, etc,.)? In this blog post we will create a simple image search feature in the Ruby on Rails application using [Weaviate](https://weaviate.io/) vector database.
![Image Description](/images/KLQ29UJS.jpeg)

The modern approach to implementing image search involves [vector embeddings](https://www.pinecone.io/learn/vector-embeddings-for-developers/). Leveraging the magic of neural networks and vector databases, we'll explore how to realize vector-based image searching.

The popularity of vector search databases has skyrocketed recently, especially for vector conversion, storage, and retrieval tasks. In this blog post, we will specifically explore one such database called [Weaviate](https://weaviate.io/), which offers neural network models like [Resnet-50](https://blog.devgenius.io/resnet50-6b42934db431)(embedding model) for vectorization.

## What is a vector database?
Type of database, that stores date as a high-dimensional value. Working with vector embeddings is more complex and the traditional databases can't keep up with it for providing insights and real-time analysis with the data. That's where vector DBs come into play, these are designed for handling this type of data and offer the performance, scalability, and flexibility you need to make the most out of your data.

![Image Description](/images/Pasted%20image%2020230724141302%201.png)

The flow will be like, first we use the embedding model to create vectors from the content, next the vector embeddings of the content is inserted into the vector database, with some reference to the original content. Now using an application we will interact with the vector DB via the embedding model, like on issuing a query we use the same embedding model to create embeddings for the query and use those to query the database for similar vector embeddings.

Our focus will be on constructing a fashion product search based on images, and to accomplish this, we will utilize the [Myntra fashion products dataset](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small) from Kaggle. Make sure to download the dataset from the provided link, as we intend to build an image search application within our Ruby on Rails environment.

Here are the high-level steps we're going to follow:

1. Implement the FashionProduct entity with active storage attachment (product_image)
2. Import the dataset from Kaggle into the fashion_products table of our application.
3. Set up Weaviate using Docker and integrate the Weaviate to ROR application using [weaviate-ruby](https://github.com/andreibondarev/weaviate-ruby) gem.
4. Create a FashionProduct class in the Weaviate client and upload the FashionProduct records from PostgreSQL to Weaviate DB.
5. Develop a user interface with image search functionality, making use of the Weaviate Client's query API capabilities.


Let's start off with creating a new Rails application (used Rails 7.0.6 and Ruby 3.2.2 for this project). We will be using docker for the application and database environments (refer to the current blog's [github repo](https://github.com/InbaKrish/fashion_products_image_search) for local setup).

```bash
rails new fashion_products_vdb --database postgresql
```

Initialize ActiveStorage for the project
```bash
rails active_storage:install
rails db:migrate
```
this should create the required tables for the ActiveStorage attachments. Since we are using local docker setup for active_storage attachments it will work using the local storage and doesn't require any cloud providers setup.

Next, let's handle the FashionProduct entity,

Create model migration for the FashionProduct entity `rails g model FashionProduct` modify the migration and the model files with the below code.
```ruby
# db/migrate/<timestamp>_create_fashion_products.rb
class CreateFashionProducts < ActiveRecord::Migration[7.0]
	def change  
		create_table :fashion_products do |t| 
			# Product ID from the dataset 
			t.integer :p_id 
			# Metadata of the products from the dataset
			t.string :gender  
			t.string :master_category      
			t.string :sub_category  
			t.string :article_type  
			t.string :base_colour  
			t.string :name  
			t.string :usage  
			  
			t.timestamps  
		end  
	end
end

# app/models/fashion_product.rb
class FashionProduct < ApplicationRecord
  has_one_attached :product_image
end
```

The FashionProduct entity should have one ActiveStorage attachment `has_one_attached :product_image` to attach the image data from the dataset.

Now migrate the fashion products data from the data set to the FashionProduct entity. For this, we need to set up a temporary volume for our application's docker service,
```yml
fashion_products_vdb-web:  
	...
	volumes:  
	- .:/fashion_products_vdb  
	- ./dataset:/dataset # Use this volume setup one time for the image dataset import process  
	...
```

then place the downloaded dataset (images directory and styles.csv file) into the dataset folder created under the projects'  root folder `fashion_products_vdb/dataset`. Restart the server, now the files under the dataset folder will be present inside the docker container (through volume config).

Now create a service class which process importing the data from the dataset folder to application's database.
```ruby
# app/services/import_fashion_product_data_service.rb

require 'csv'

class ImportFashionProductDataService
  def initialize(dataset_path, metadata_file_name, image_dir)
    @dataset_path = dataset_path
    @csv_metadata_path = File.join(@dataset_path, metadata_file_name)
    @image_dir = File.join(@dataset_path, image_dir)
  end

  def call
    process_csv_data_import
  end

  private

  def process_csv_data_import
    line_number = 0

    begin
      CSV.foreach(@csv_metadata_path, headers: true) do |row_data|
        create_fashion_prd_from_metadata(format_metadata(row_data))
        line_number += 1
      end
    rescue StandardError => e
      puts "Error parsing CSV at line #{line_number}: #{e.message}"
    end
  end

  # Create a new record with the image from CSV metadata
  def create_fashion_prd_from_metadata(metadata)
    fsprd = create_fashion_prd_with(attributes: metadata)

    # Image attachment process
    image_file  = File.join(@image_dir, fsprd.p_id.to_s + '.jpg')
    puts image_file
    return unless File.exist?(image_file)

    fsprd.product_image.attach(io: File.open(image_file), filename: File.basename(image_file))
    fsprd.save
    puts "#{fsprd.name} created successfully."
  end

  def format_metadata(row_data)
    metadata = row_data.to_hash
    metadata = metadata.transform_keys do |k|
      case k.to_s
      when 'productDisplayName'
        'name'
      when 'id'
        'p_id'
      else
        k.to_s.underscore
      end
    end
    metadata
  end

  def create_fashion_prd_with(attributes:)
    FashionProduct.new.tap do |record|
      attributes.each do |k, v|
        next unless record.respond_to?(k + '=')

        record.send(k + '=', v)
      end
    end
  end
end
```

The above service class will loop over all the rows inside the `styles.csv` from the dataset which contains the product metadata and takes the corresponding image from the images folder (via the product's id in the CSV file) and creates the FashionProduct entry with those data.

Open rails console and call the service class instance's call method once to import the data to the application's database.
```bash
docker-compose exec fashion_products_vdb-web bash
=> rails console
```

```ruby
ImportFashionProductDataService.new('\dataset', 'styles.csv', 'images')
```

Now we are moving to the Weaviate integration part, for the Weaviate client setup we can use [Weaviate's docker-compose configurator](https://weaviate.io/developers/weaviate/installation/docker-compose) to generate docker-compose.yml file for our specific need. We are going to use image to vector conversion so use the below config and download the docker-compose file.
![Image Description](/images/weaviate_img2vec_docker-compose_config.gif)

The docker-compose file will contain two services, weaviate (the VDB and Weavite APIs service) and the image to vector neural network service (resnet50 pytorch). Since we are using docker service for the ruby application as well combine all the services under one docker-compose file like,
```yml
---  
version: '3.4'  
services:  
	weaviate:  
		command:  
		- --host  
		- 0.0.0.0  
		- --port  
		- '8080'  
		- --scheme  
		- http  
		image: semitechnologies/weaviate:1.19.11  
		ports:  
		- 8080:8080  
		restart: on-failure:0  
		volumes:  
			- /var/weaviate:/var/lib/weaviate  
		environment:  
			IMAGE_INFERENCE_API: 'http://i2v-neural:8080'  
			QUERY_DEFAULTS_LIMIT: 25  
			AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'  
			PERSISTENCE_DATA_PATH: '/var/lib/weaviate'  
			DEFAULT_VECTORIZER_MODULE: 'img2vec-neural'  
			ENABLE_MODULES: 'img2vec-neural'  
			CLUSTER_HOSTNAME: 'node1'  
	i2v-neural:  
		image: semitechnologies/img2vec-pytorch:resnet50  
		environment:  
			ENABLE_CUDA: '0'  
	database:  
		image: postgres  
		container_name: database  
		env_file:  
		- .env  
		volumes:  
		- ./tmp/db:/var/lib/postgresql/data  
		ports:  
		- 6000:5432  
	fashion_products_vdb-web:  
		container_name: fashion_products_vdb-web  
		build: .  
		depends_on:  
		- database  
		- weaviate  
		- i2v-neural  
		env_file:  
		- .env  
		command: bash -c "bundle && rm -f /fashion_products_vdb/tmp/pids/server.pid && rails db:prepare && rails server -b 0.0.0.0"  
		volumes:  
		- .:/fashion_products_vdb  
		# - ./dataset:/dataset # Use this volume setup one time for the image dataset import process  
		ports:  
		- 3012:3000  
		tty: true  
		stdin_open: true  
...
```

By default the weaviate service does not contain any volumes option, we are adding the `/var/weaviate:/var/lib/weaviate` volume in order to persist the weaviate changes even after docker container restart. 

After the docker-compose file modifications run the `docker-compose up` command, it should download the images for the weaviate dependant services (note: the image sizes will be around 7GB for the `resnet-50` image)

Now add the [weaviate-ruby](https://github.com/andreibondarev/weaviate-ruby) gem to the project's Gemfile,
```
# Weaviate.io API ruby wrapper  
gem "weaviate-ruby"
```

Create a library class to create Weaviate client instance for our application,
```ruby
# lib/weaviate_client.rb

require "weaviate"

class WeaviateClient
  # Creates a new WeaviateClient instance with the specified configuration
  def self.create_client
    Weaviate::Client.new(
      url: "http://weaviate:8080"             # Use ENV variables
    )
  end
end
```

Since we are using local docker setup we can use the port 8080 with weavite host  for the client communication. Weaviate also provide's cloud instances for which we need to generate API key for the client communication.

Add lib path to the application.rb -> autoload_path config as `config.autoload_paths += %W(#{config.root}/lib)` in order to load the class file to use in other parts of the application.

Next create FashionProduct class schema using rails migration that will hold our FashionProduct product_image vectors and ID.
```bash
rails g migration weaviate_create_fashion_product_class
```

```ruby
# db/migrate/20230706115924_weaviate_create_fashion_product_class.rb

class WeaviateCreateFashionProductClass < ActiveRecord::Migration[7.0]
  def up
    class_name = 'FashionProduct'        # Name of the class (in vector DB)
    weaviate_client = WeaviateClient.create_client
    begin
      if weaviate_client.schema.get(class_name: class_name) != "Not Found"
        puts "Class '#{class_name}' already exists"
        return
      end

      weaviate_client.schema.create(
          class_name: class_name,
          vectorizer: 'img2vec-neural',   # Module used to vectorize the images
          module_config: {
            'img2vec-neural': {           # Weaviate's img2vec module
              'imageFields': [
                'image'
              ]
            }
          },
          properties: [                   # Properties of the VDB class
            {
              'name': 'image',
              'dataType': ['blob']
            },
            {
              'name': 'fashion_prd_id',
              'dataType': ['int']
            }
        ]
      )
    rescue => exception
      if weaviate_client.schema.get(class_name: class_name) != "Not Found"
        weaviate_client.schema.delete(class_name: class_name)
      end
      raise exception
    end
  end

  def down
    weaviate_client = WeaviateClient.create_client
    if weaviate_client.schema.get(class_name: 'FashionProduct') != "Not Found"
      weaviate_client.schema.delete(class_name: 'FashionProduct')
    end
  end
end
```

Weaviate's Schema contains the structure of the classes (similar to db tables). Each class contains properties (similar to table columns), we are using two properties `image` with blob datatype (to store the image vectors) and `fashion_prd_id` with integer datatype. If we want to delete a class under the schema along with all the data under the class we can use the schema - delete API as used in the `down` method of the migration.

Now we will import the images to Weaviate DB. Using Weaviate objects batch create API we can import the image objects to Weaviate DB, the vector conversion of the images before storing will be handled by the Weaviate for which is uses the resnet-50 image APIs.

Create a one time rake to import the FashionProduct data into Weaviate DB.
```ruby
task import_fashion_prd_data_to_weaviate: :environment do
  weaviate_client = WeaviateClient.create_client

  FashionProduct.find_in_batches(batch_size: 500) do |fpds|
    # Generate array with FashionProduct Base64 encoded image and ID values
    objects_to_upload = fpds.map do |fpd|
      {
        class: 'FashionProduct',
        properties: {
          image: Base64.strict_encode64(fpd.product_image_attachment.download).to_s,
          fashion_prd_id: fpd.id
        }
      }
    end

    # Weaviate.io objects API batch import
    p weaviate_client.objects.batch_create(
      objects: objects_to_upload
    )
  end

  puts "-- Total FashionProduct records: #{FashionProduct.count}"

  uploaded_count = weaviate_client.query.aggs(
    class_name: 'FashionProduct', 
    fields: 'meta { count }',
  )

  puts "-- Total objects uploaded to Weaviate DB: #{uploaded_count}"
end
```

Now we are coming to the final stage, searching the image data with an image input. We will use the Weaviate client's query API to get the matching image records, for which we will be passing a Base64 encoded image value for the `near_image`  attribute.
```ruby
require 'open-uri'
weaviate_client_inst = WeaviateClient.create_client

test_img_url = '<URL of the image>'
base_64_img_string = Base64.strict_encode64(URI.parse(test_img_url).read)

result = weaviate_client_inst.query.get(
class_name: 'FashionProduct',
limit: '5',
offset: '1',
near_image: "{ image: \"#{base_64_img_string}\" }",
fields: 'fashion_prd_id'
)

## result
[{"fashion_prd_id"=>10655}, {"fashion_prd_id"=>3077}, {"fashion_prd_id"=>207}, {"fashion_prd_id"=>11834}, {"fashion_prd_id"=>7883}]


## FashionProducts stored in application database
FashionProduct.where(id: result.map { |prd_val| prd_val['fashion_prd_id'] })
```

At last, we will build a simple UI that renders a form to get the image file from the user, and based on the search we will display all the matching FashionProduct items. Refer to the commits ([FashionProducts UI dev](https://github.com/InbaKrish/fashion_products_image_search/commit/87afc73d43f49bf534d9ccc5192d366fb743db79) and [Image search controller with UI](https://github.com/InbaKrish/fashion_products_image_search/commit/40a22ae46d759cb518d618d8d0d2d8e33fc11f39))

## Conclusion






